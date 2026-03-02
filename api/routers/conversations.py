"""Conversation persistence and AI feedback/correction routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_current_user
from api.schemas import (
    SaveConversationRequest,
    ConversationSummary,
    ConversationDetail,
    FeedbackRequest,
    CorrectionRequest,
    CorrectionSchema,
)
from api.core import db

logger = logging.getLogger("sehra.routers.conversations")
router = APIRouter()


# --- Conversation Endpoints ---

@router.post("/conversations", response_model=ConversationDetail)
def save_conversation(req: SaveConversationRequest, user: dict = Depends(get_current_user)):
    """Save or update a copilot conversation."""
    conversation_id = db.save_conversation(
        conversation_id=req.id,
        user=user["sub"],
        title=req.title,
        messages=req.messages,
        sehra_id=req.sehra_id,
        sehra_label=req.sehra_label,
    )
    convo = db.get_conversation(conversation_id, user["sub"])
    if not convo:
        raise HTTPException(status_code=500, detail="Failed to save conversation.")
    return convo


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(user: dict = Depends(get_current_user)):
    """List all conversations for the current user (summary only)."""
    return db.list_conversations(user["sub"])


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, user: dict = Depends(get_current_user)):
    """Get a full conversation with messages."""
    convo = db.get_conversation(conversation_id, user["sub"])
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return convo


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, user: dict = Depends(get_current_user)):
    """Delete a conversation."""
    deleted = db.delete_conversation(conversation_id, user["sub"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found.")


# --- Feedback Endpoints ---

@router.post("/feedback", status_code=201)
def submit_feedback(req: FeedbackRequest, user: dict = Depends(get_current_user)):
    """Submit thumbs up/down on an AI message."""
    if req.rating not in ("up", "down"):
        raise HTTPException(status_code=400, detail="Rating must be 'up' or 'down'.")
    feedback_id = db.save_ai_feedback(
        user=user["sub"],
        message_id=req.message_id,
        conversation_id=req.conversation_id,
        rating=req.rating,
        comment=req.comment,
    )
    return {"id": feedback_id}


# --- Correction Endpoints ---

@router.post("/corrections", status_code=201)
def submit_correction(req: CorrectionRequest, user: dict = Depends(get_current_user)):
    """Submit a text correction for an AI-generated response."""
    correction_id = db.save_ai_correction(
        user=user["sub"],
        original_text=req.original_text,
        corrected_text=req.corrected_text,
        context=req.context,
        sehra_id=req.sehra_id,
        message_id=req.message_id,
    )
    return {"id": correction_id}


@router.get("/corrections", response_model=list[CorrectionSchema])
def get_corrections(
    user: dict = Depends(get_current_user),
    sehra_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Get corrections for copilot context enrichment."""
    return db.get_ai_corrections(user=None, sehra_id=sehra_id, limit=limit)
