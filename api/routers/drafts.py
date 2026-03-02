"""Form draft save/load/delete routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user
from api.schemas import FormDraftSchema, SaveDraftRequest
from api.core import db

logger = logging.getLogger("sehra.routers.drafts")
router = APIRouter()


@router.get("/drafts", response_model=FormDraftSchema | None)
def get_draft(user: dict = Depends(get_current_user)):
    draft = db.get_form_draft(user["sub"])
    return draft


@router.put("/drafts", response_model=FormDraftSchema)
def save_draft(req: SaveDraftRequest, user: dict = Depends(get_current_user)):
    draft_id = db.save_form_draft(user["sub"], req.section_progress, req.responses)
    draft = db.get_form_draft(user["sub"])
    return draft


@router.delete("/drafts", status_code=204)
def delete_draft(user: dict = Depends(get_current_user)):
    db.delete_form_draft(user["sub"])
