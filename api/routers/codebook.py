"""Admin codebook management routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from api.deps import get_current_user, require_admin
from api.schemas import CodebookItemSchema, AddCodebookItemRequest, UpdateCodebookItemRequest
from api.core.codebook_admin import get_sections, get_items_by_section, add_item, update_item, remove_item

logger = logging.getLogger("sehra.routers.codebook")
router = APIRouter()


@router.get("/codebook/sections")
def list_sections(
    response: Response,
    country: Optional[str] = Query(default=None, description="Country-specific codebook"),
    user: dict = Depends(get_current_user),
):
    """List codebook sections. Pass country to get country-specific sections."""
    response.headers["Cache-Control"] = "private, max-age=60, stale-while-revalidate=120"
    return get_sections(country=country)


@router.get("/codebook/items", response_model=list[CodebookItemSchema])
def list_items(
    section: str,
    response: Response,
    country: Optional[str] = Query(default=None, description="Country-specific codebook"),
    user: dict = Depends(get_current_user),
):
    """List codebook items for a section. Pass country to get country-specific items."""
    response.headers["Cache-Control"] = "private, max-age=60, stale-while-revalidate=120"
    return get_items_by_section(section, country=country)


@router.post("/codebook/items", response_model=CodebookItemSchema)
def create_item(req: AddCodebookItemRequest, user: dict = Depends(require_admin)):
    """Add a codebook item. Use country field in request body for country-specific codebook."""
    item = add_item(
        section=req.section,
        question=req.question,
        item_type=req.type,
        has_scoring=req.has_scoring,
        is_reverse=req.is_reverse,
        item_id=req.item_id or "",
        country=req.country,
    )
    return item


@router.patch("/codebook/items/{item_id}")
def patch_item(
    item_id: str,
    req: UpdateCodebookItemRequest,
    country: Optional[str] = Query(default=None, description="Country-specific codebook"),
    user: dict = Depends(require_admin),
):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    success = update_item(item_id, country=country, **updates)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}


@router.delete("/codebook/items/{item_id}", status_code=204)
def delete_item(
    item_id: str,
    country: Optional[str] = Query(default=None, description="Country-specific codebook"),
    user: dict = Depends(require_admin),
):
    success = remove_item(item_id, country=country)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
