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


@router.post("/agent/chat")
async def agent_chat(
    request: AgentChatRequest,
    user: dict = Depends(get_current_user),
):
    """Stream copilot responses via Server-Sent Events.

    Accepts conversation messages and optional context (sehra_id, page).
    Returns SSE events: thinking, tool_call, tool_result, message, chart, actions, error, done.
    """
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
        ),
        media_type="text/event-stream",
    )
