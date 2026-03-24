"""Audit log router: view copilot action history and rollback changes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.core.db import get_audit_log, rollback_action
from api.deps import get_current_user

logger = logging.getLogger("sehra.routers.audit")

router = APIRouter()


@router.get("/audit/{sehra_id}")
def get_sehra_audit_log(
    sehra_id: str,
    user: Optional[str] = Query(None, description="Filter by username"),
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
):
    """Get the audit log for a specific SEHRA assessment.

    Returns a list of copilot tool actions performed on this SEHRA,
    ordered by most recent first.
    """
    entries = get_audit_log(sehra_id=sehra_id, user=user, limit=limit)
    return {"sehra_id": sehra_id, "entries": entries, "count": len(entries)}


@router.post("/audit/{audit_id}/rollback")
def rollback_audit_action(
    audit_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Rollback a specific copilot action by restoring the previous value.

    Only works for write actions (edit_entry, edit_report_section,
    edit_executive_summary, change_status) that have not already been rolled back.
    """
    result = rollback_action(audit_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Rollback failed"),
        )
    logger.info(
        "User '%s' rolled back audit entry %s",
        current_user.get("sub"),
        audit_id,
    )
    return result
