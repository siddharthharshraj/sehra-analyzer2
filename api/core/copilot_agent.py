"""Agentic copilot loop using Groq/OpenAI with function calling.

Streams SSE events as the agent reasons, calls tools, and produces a final response.
Uses Groq (llama-3.3-70b) when GROQ_API_KEY is set, falls back to OpenAI gpt-4o.
"""

import json
import logging
from typing import AsyncGenerator

from openai import OpenAI

from api.config import get_settings
from api.core.agent_tools import TOOL_SCHEMAS, execute_tool
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


def _sse_event(event_type: str, data: dict) -> str:
    """Format SSE event payload. sse-starlette adds the 'data:' prefix automatically."""
    return json.dumps({"type": event_type, **data}, default=str)


async def run_copilot(
    messages: list[dict],
    sehra_id: str | None = None,
    page_context: str | None = None,
) -> AsyncGenerator[str, None]:
    """Run the agentic copilot loop, yielding SSE events.

    Events:
        thinking   - Agent is reasoning
        tool_call  - Tool being invoked
        tool_result - Tool output (truncated)
        message    - Final text response
        chart      - Chart specification
        actions    - Suggested action buttons
        error      - Error occurred
        done       - Stream complete
    """
    settings = get_settings()

    # Use Groq when available, fall back to OpenAI
    if settings.groq_api_key:
        client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        model = "llama-3.3-70b-versatile"
    else:
        client = OpenAI(api_key=settings.openai_api_key)
        model = "gpt-4o"

    # Build system message with context
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

    # Build conversation with system prompt
    api_messages = [{"role": "system", "content": system_content}]
    for msg in messages:
        api_messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
        })

    yield _sse_event("thinking", {"text": "Analyzing your request..."})

    try:
        for _round in range(MAX_TOOL_ROUNDS):
            response = client.chat.completions.create(
                model=model,
                messages=api_messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=4096,
            )

            choice = response.choices[0]
            finish_reason = choice.finish_reason

            # If the model wants to call tools
            if choice.message.tool_calls:
                # Add assistant message with tool calls
                # Build a clean dict with only standard fields to avoid
                # provider-specific extras (annotations, audio, etc.)
                clean_tool_calls = []
                for tc in choice.message.tool_calls:
                    clean_tool_calls.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments or "{}",
                        },
                    })
                api_messages.append({
                    "role": "assistant",
                    "content": choice.message.content,
                    "tool_calls": clean_tool_calls,
                })

                for tool_call in choice.message.tool_calls:
                    func_name = tool_call.function.name
                    try:
                        func_args = json.loads(tool_call.function.arguments) or {}
                    except (json.JSONDecodeError, TypeError):
                        func_args = {}

                    yield _sse_event("tool_call", {
                        "tool": func_name,
                        "arguments": func_args,
                    })

                    # Execute the tool
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
                        "tool_call_id": tool_call.id,
                        "content": result_str,
                    })

                    # Check for actions in suggest_actions results
                    if func_name == "suggest_actions" and "actions" in result:
                        yield _sse_event("actions", {"actions": result["actions"]})

                # Continue the loop to let the model process tool results
                continue

            # No tool calls - model is done
            content = choice.message.content or ""

            # Extract chart specs from the response
            chart_spec = _extract_chart_spec(content)
            if chart_spec:
                yield _sse_event("chart", {"spec": chart_spec})
                # Remove the chart block from the message text
                content = _remove_chart_block(content)

            yield _sse_event("message", {"text": content.strip()})
            break

        else:
            # Exhausted tool rounds
            yield _sse_event("message", {
                "text": "I've gathered the data but reached my processing limit. Here's what I found so far."
            })

    except Exception as e:
        logger.exception("Copilot error")
        yield _sse_event("error", {"text": str(e)})

    yield _sse_event("done", {})


def _extract_chart_spec(text: str) -> dict | None:
    """Extract a chart spec from ```chart ... ``` blocks."""
    import re
    match = re.search(r"```chart\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return None
    return None


def _remove_chart_block(text: str) -> str:
    """Remove ```chart ... ``` blocks from text."""
    import re
    return re.sub(r"```chart\s*\n?.*?\n?```", "", text, flags=re.DOTALL).strip()
