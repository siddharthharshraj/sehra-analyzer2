"""Agentic copilot loop with SSE streaming.

Orchestrates the agent reasoning loop, tool execution, and confirmation flow.
LLM provider management is in agent_llm.py; tool definitions in agent_tools.py.

Token-level streaming: LLM responses are streamed chunk-by-chunk as message_delta events,
with a final message event containing the full assembled text.

Confirmation flow: Write operations (edits, status changes, batch approve) require user
confirmation before execution. The agent yields a confirmation_required event and stops.
The frontend sends back a confirmed_tool_call_id to resume execution.
"""

import json
import logging
import re
import time
import threading
from typing import AsyncGenerator

from api.core.agent_llm import get_llm_client, stream_llm_response
from api.core.agent_tools import (
    WRITE_TOOLS,
    execute_tool,
    get_confirmation_preview,
)
from api.core.db import get_corrections_for_context

logger = logging.getLogger("sehra.copilot_agent")

SYSTEM_PROMPT = """You are the SEHRA Copilot, an AI assistant embedded in the School Eye Health Rapid Assessment (SEHRA) Analysis Platform.

Your role is to help users understand their SEHRA assessment data, provide insights, and **directly edit analysis when asked**.

You have tools to both **read** and **write** assessment data. Use them to answer questions and apply edits.

Guidelines:
- When the user mentions "this assessment" or similar, use the sehra_id from context.
- Always call tools to get real data before answering - never fabricate data.
- Present numbers, comparisons, and summaries clearly.
- **When the user asks to change, fix, edit, or reclassify anything, use the write tools to apply the change directly.** Confirm what you changed afterwards.
- You can edit: qualitative entry theme/classification, report sections, executive summaries, assessment status, and batch approve entries.
- When suggesting actions, use the suggest_actions tool to get actionable buttons.
- For charts, return a chart_spec in your final message when visualization would help.
- Keep responses concise but thorough.
- Use markdown formatting for readability.

Chart spec format (include in your response text as a JSON block when helpful):
```chart
{"type": "bar|pie|radar", "title": "Chart Title", "data": [{"label": "X", "value": 10}]}
```
"""

MAX_TOOL_ROUNDS = 8

# ---------------------------------------------------------------------------
# Pending tool call store (for confirmation flow)
# ---------------------------------------------------------------------------

_pending_tool_calls: dict[str, dict] = {}
_pending_lock = threading.Lock()
_PENDING_TTL_SECONDS = 300  # 5 minutes


def _cleanup_expired_pending():
    """Remove pending tool calls older than TTL."""
    now = time.time()
    with _pending_lock:
        expired = [
            k for k, v in _pending_tool_calls.items()
            if now - v["created_at"] > _PENDING_TTL_SECONDS
        ]
        for k in expired:
            del _pending_tool_calls[k]


def store_pending_tool_call(tool_call_id: str, tool_name: str, args: dict,
                            api_messages: list[dict]):
    """Store a pending write tool call awaiting user confirmation."""
    _cleanup_expired_pending()
    with _pending_lock:
        _pending_tool_calls[tool_call_id] = {
            "tool_name": tool_name,
            "args": args,
            "api_messages": api_messages,
            "created_at": time.time(),
        }


def pop_pending_tool_call(tool_call_id: str) -> dict | None:
    """Retrieve and remove a pending tool call. Returns None if expired or not found."""
    _cleanup_expired_pending()
    with _pending_lock:
        return _pending_tool_calls.pop(tool_call_id, None)


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------


def _sse_event(event_type: str, data: dict) -> str:
    """Format SSE event payload. sse-starlette adds the 'data:' prefix automatically."""
    return json.dumps({"type": event_type, **data}, default=str)


# ---------------------------------------------------------------------------
# Shared tool processing loop
# ---------------------------------------------------------------------------


def _build_system_content(sehra_id: str | None, page_context: str | None) -> str:
    """Build the system prompt with optional context."""
    system_content = SYSTEM_PROMPT
    if sehra_id:
        system_content += f"\n\nCurrent assessment context: sehra_id = {sehra_id}"
    if page_context:
        system_content += f"\nUser is currently on: {page_context}"

    # Inject recent user corrections so the agent learns from past edits
    try:
        corrections = get_corrections_for_context(sehra_id=sehra_id, limit=10)
        if corrections:
            correction_lines = []
            for c in corrections:
                correction_lines.append(
                    f'- "{c["original_text"][:100]}" should be "{c["corrected_text"][:100]}" ({c.get("context", "")})'
                )
            system_content += (
                "\n\nPrevious user corrections (learn from these and apply similar fixes):\n"
                + "\n".join(correction_lines)
            )
    except Exception:
        pass  # Non-critical - don't break the agent if corrections fail

    return system_content


async def _run_agent_loop(
    api_messages: list[dict],
) -> AsyncGenerator[str, None]:
    """Core agent loop: stream LLM, handle tool calls, yield SSE events.

    Shared between initial requests and confirmation resumptions.
    """
    client, model = get_llm_client()

    for _round in range(MAX_TOOL_ROUNDS):
        # Stream the LLM response token-by-token
        assembled = None
        for event_type, data in stream_llm_response(client, model, api_messages):
            if event_type == "_assembled":
                assembled = data
            elif event_type == "message_delta":
                yield _sse_event("message_delta", data)

        if assembled is None:
            yield _sse_event("error", {"text": "Stream produced no response"})
            break

        content = assembled["content"]
        tool_calls = assembled["tool_calls"]

        # If the model wants to call tools
        if tool_calls:
            clean_tool_calls = []
            for tc in tool_calls:
                clean_tool_calls.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"] or "{}",
                    },
                })
            api_messages.append({
                "role": "assistant",
                "content": content or None,
                "tool_calls": clean_tool_calls,
            })

            for tc in tool_calls:
                func_name = tc["name"]
                try:
                    func_args = json.loads(tc["arguments"]) or {}
                except (json.JSONDecodeError, TypeError):
                    func_args = {}

                # Check if this is a write tool requiring confirmation
                if func_name in WRITE_TOOLS:
                    preview_data = get_confirmation_preview(func_name, func_args)
                    store_pending_tool_call(
                        tool_call_id=tc["id"],
                        tool_name=func_name,
                        args=func_args,
                        api_messages=list(api_messages),  # snapshot
                    )
                    yield _sse_event("confirmation_required", {
                        "tool_call_id": tc["id"],
                        "tool_name": func_name,
                        "description": preview_data["description"],
                        "args": func_args,
                        "preview": preview_data["preview"],
                    })
                    yield _sse_event("done", {})
                    return  # Stop the agent loop; wait for confirmation

                # Read tool: execute immediately
                yield _sse_event("tool_call", {
                    "tool": func_name,
                    "arguments": func_args,
                })

                result = execute_tool(func_name, func_args)

                # Truncate large results to stay within LLM token limits
                result_str = json.dumps(result, default=str)
                if len(result_str) > 8000:
                    result_str = result_str[:8000] + '..."}'
                preview = result_str[:500] + "..." if len(result_str) > 500 else result_str

                yield _sse_event("tool_result", {
                    "tool": func_name,
                    "preview": preview,
                })

                # Feed result back to the model
                api_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_str,
                })

                # Check for actions in suggest_actions results
                if func_name == "suggest_actions" and "actions" in result:
                    yield _sse_event("actions", {"actions": result["actions"]})

            # Continue the loop to let the model process tool results
            continue

        # No tool calls - model is done. Emit the final assembled message.
        chart_spec = _extract_chart_spec(content)
        if chart_spec:
            yield _sse_event("chart", {"spec": chart_spec})
            content = _remove_chart_block(content)

        yield _sse_event("message", {"text": content.strip()})
        return

    # Exhausted tool rounds
    yield _sse_event("message", {
        "text": "I've gathered the data but reached my processing limit. Here's what I found so far."
    })


# ---------------------------------------------------------------------------
# Main copilot entry point
# ---------------------------------------------------------------------------


async def run_copilot(
    messages: list[dict],
    sehra_id: str | None = None,
    page_context: str | None = None,
    confirmed_tool_call_id: str | None = None,
    confirmed_args: dict | None = None,
) -> AsyncGenerator[str, None]:
    """Run the agentic copilot loop, yielding SSE events.

    Events:
        thinking             - Agent is reasoning
        message_delta        - Incremental text token from the LLM
        tool_call            - Tool being invoked
        tool_result          - Tool output (truncated)
        confirmation_required - Write tool needs user confirmation
        message              - Final assembled text response
        chart                - Chart specification
        actions              - Suggested action buttons
        error                - Error occurred
        done                 - Stream complete
    """
    # Handle confirmation resumption
    if confirmed_tool_call_id:
        async for event in _resume_confirmed_tool_call(
            confirmed_tool_call_id, confirmed_args, messages, sehra_id, page_context
        ):
            yield event
        return

    # Build conversation with system prompt
    system_content = _build_system_content(sehra_id, page_context)
    api_messages = [{"role": "system", "content": system_content}]
    for msg in messages:
        api_messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
        })

    yield _sse_event("thinking", {"text": "Analyzing your request..."})

    try:
        async for event in _run_agent_loop(api_messages):
            yield event
    except Exception as e:
        logger.exception("Copilot error")
        yield _sse_event("error", {"text": str(e)})

    yield _sse_event("done", {})


# ---------------------------------------------------------------------------
# Confirmation resumption
# ---------------------------------------------------------------------------


async def _resume_confirmed_tool_call(
    tool_call_id: str,
    confirmed_args: dict | None,
    messages: list[dict],
    sehra_id: str | None,
    page_context: str | None,
) -> AsyncGenerator[str, None]:
    """Resume execution after user confirms a write tool call.

    Executes the stored tool, feeds the result back to the LLM, and continues
    the agent loop to produce a final response.
    """
    pending = pop_pending_tool_call(tool_call_id)
    if not pending:
        yield _sse_event("error", {
            "text": "Confirmation expired or not found. Please try your request again."
        })
        yield _sse_event("done", {})
        return

    tool_name = pending["tool_name"]
    # Allow the frontend to override args (e.g., user tweaked values)
    args = confirmed_args if confirmed_args is not None else pending["args"]
    api_messages = pending["api_messages"]

    yield _sse_event("thinking", {"text": f"Executing {tool_name}..."})

    # Execute the confirmed tool
    yield _sse_event("tool_call", {"tool": tool_name, "arguments": args})

    result = execute_tool(tool_name, args)
    result_str = json.dumps(result, default=str)
    if len(result_str) > 8000:
        result_str = result_str[:8000] + '..."}'
    preview = result_str[:500] + "..." if len(result_str) > 500 else result_str

    yield _sse_event("tool_result", {"tool": tool_name, "preview": preview})

    # Feed the tool result back into the conversation
    api_messages.append({
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": result_str,
    })

    # Continue the agent loop so the LLM can summarize what happened
    try:
        async for event in _run_agent_loop(api_messages):
            yield event
    except Exception as e:
        logger.exception("Copilot resume error")
        yield _sse_event("error", {"text": str(e)})

    yield _sse_event("done", {})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_chart_spec(text: str) -> dict | None:
    """Extract a chart spec from ```chart ... ``` blocks."""
    match = re.search(r"```chart\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return None
    return None


def _remove_chart_block(text: str) -> str:
    """Remove ```chart ... ``` blocks from text."""
    return re.sub(r"```chart\s*\n?.*?\n?```", "", text, flags=re.DOTALL).strip()
