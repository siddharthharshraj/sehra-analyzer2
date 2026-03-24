"""LLM provider management and streaming for the SEHRA Copilot.

Handles provider selection (Groq / OpenAI) and token-level streaming
with tool call argument accumulation.
"""

import logging

from openai import OpenAI

from api.config import get_settings
from api.core.agent_tools import TOOL_SCHEMAS

logger = logging.getLogger("sehra.agent_llm")


def get_llm_client() -> tuple[OpenAI, str]:
    """Return the configured LLM client and model name.

    Uses Groq (llama-3.3-70b) when GROQ_API_KEY is set,
    falls back to OpenAI gpt-4o.
    """
    settings = get_settings()

    if settings.groq_api_key:
        client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        model = "llama-3.3-70b-versatile"
    else:
        client = OpenAI(api_key=settings.openai_api_key)
        model = "gpt-4o"

    return client, model


def stream_llm_response(client: OpenAI, model: str, api_messages: list[dict]):
    """Stream an LLM response, yielding (event_type, data) tuples.

    Handles both text content streaming and tool call argument accumulation.

    Yields:
        ("message_delta", {"text": str}) for each text chunk
        ("_assembled", {...}) as the final item with full content, tool_calls, finish_reason
    """
    stream = client.chat.completions.create(
        model=model,
        messages=api_messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        temperature=0.3,
        max_tokens=4096,
        stream=True,
    )

    full_content = ""
    tool_calls_acc: dict[int, dict] = {}  # index -> {id, name, arguments}
    finish_reason = None

    for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta
        finish_reason = chunk.choices[0].finish_reason or finish_reason

        # Accumulate text content
        if delta.content:
            full_content += delta.content
            yield ("message_delta", {"text": delta.content})

        # Accumulate tool calls (arguments arrive in pieces)
        if delta.tool_calls:
            for tc_delta in delta.tool_calls:
                idx = tc_delta.index
                if idx not in tool_calls_acc:
                    tool_calls_acc[idx] = {
                        "id": tc_delta.id or "",
                        "name": "",
                        "arguments": "",
                    }
                if tc_delta.id:
                    tool_calls_acc[idx]["id"] = tc_delta.id
                if tc_delta.function:
                    if tc_delta.function.name:
                        tool_calls_acc[idx]["name"] = tc_delta.function.name
                    if tc_delta.function.arguments:
                        tool_calls_acc[idx]["arguments"] += tc_delta.function.arguments

    # Build final tool_calls list sorted by index
    assembled_tool_calls = None
    if tool_calls_acc:
        assembled_tool_calls = [
            tool_calls_acc[idx]
            for idx in sorted(tool_calls_acc.keys())
        ]

    yield ("_assembled", {
        "content": full_content,
        "tool_calls": assembled_tool_calls,
        "finish_reason": finish_reason or "stop",
    })
