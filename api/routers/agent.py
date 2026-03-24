"""SSE endpoint for the SEHRA Copilot agent."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from api.deps import get_current_user
from api.core.copilot_agent import run_copilot

logger = logging.getLogger("sehra.routers.agent")

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class AgentChatRequest(BaseModel):
    messages: list[ChatMessage]
    sehra_id: Optional[str] = None
    page_context: Optional[str] = None
    confirmed_tool_call_id: Optional[str] = None
    confirmed_args: Optional[dict] = None


@router.post("/agent/chat")
async def agent_chat(
    request: AgentChatRequest,
    user: dict = Depends(get_current_user),
):
    """Stream copilot responses via Server-Sent Events.

    Accepts conversation messages and optional context (sehra_id, page).
    Returns SSE events: thinking, message_delta, tool_call, tool_result,
    confirmation_required, message, chart, actions, error, done.

    Confirmation flow:
        1. When the agent wants to call a write tool, it emits a
           confirmation_required event with tool_call_id, description, and preview.
        2. The frontend displays a confirmation dialog to the user.
        3. If confirmed, the frontend sends a new request with the same messages
           plus confirmed_tool_call_id (and optionally confirmed_args to override).
        4. The agent executes the tool and continues.
    """
    if request.confirmed_tool_call_id:
        logger.info(
            "Copilot confirm: user=%s, tool_call_id=%s",
            user.get("sub"),
            request.confirmed_tool_call_id,
        )
    else:
        logger.info(
            "Copilot chat: user=%s, sehra_id=%s, messages=%d",
            user.get("sub"),
            request.sehra_id,
            len(request.messages),
        )

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    return EventSourceResponse(
        run_copilot(
            messages=messages,
            sehra_id=request.sehra_id,
            page_context=request.page_context,
            confirmed_tool_call_id=request.confirmed_tool_call_id,
            confirmed_args=request.confirmed_args,
        ),
        media_type="text/event-stream",
    )
