"""SEHRA CRUD operations router."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import get_current_user
from api.schemas import (
    SEHRASummary,
    SEHRADetail,
    ComponentAnalysisSchema,
    QualitativeEntrySchema,
    ReportSectionSchema,
    UpdateEntryRequest,
    UpdateSectionRequest,
    UpdateSehraRequest,
    UpdateStatusRequest,
    BatchApproveRequest,
    BatchApproveResponse,
)
from api.core.db import (
    list_sehras,
    get_sehra,
    delete_sehra,
    update_sehra_fields,
    update_sehra_status,
    get_component_analyses,
    get_executive_summary,
    update_qualitative_entry,
    update_report_section,
    batch_approve_entries,
)

logger = logging.getLogger("sehra.routers.sehras")

router = APIRouter()


@router.get("/sehras", response_model=list[SEHRASummary])
def list_all_sehras(response: Response, user: dict = Depends(get_current_user)):
    """List all SEHRA assessments."""
    response.headers["Cache-Control"] = "private, max-age=10, stale-while-revalidate=30"
    results = list_sehras()
    return [SEHRASummary(**s) for s in results]


@router.get("/sehras/{sehra_id}", response_model=SEHRADetail)
def get_sehra_detail(sehra_id: str, response: Response, user: dict = Depends(get_current_user)):
    """Get detailed SEHRA information including executive summary."""
    response.headers["Cache-Control"] = "private, max-age=5, stale-while-revalidate=15"
    sehra = get_sehra(sehra_id)
    if not sehra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SEHRA '{sehra_id}' not found.",
        )
    return SEHRADetail(**sehra)


@router.delete("/sehras/{sehra_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_sehra(sehra_id: str, user: dict = Depends(get_current_user)):
    """Delete a SEHRA and all related data."""
    sehra = get_sehra(sehra_id)
    if not sehra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SEHRA '{sehra_id}' not found.",
        )
    delete_sehra(sehra_id)
    logger.info("User '%s' deleted SEHRA '%s'", user["sub"], sehra_id)


@router.patch("/sehras/{sehra_id}", response_model=SEHRADetail)
def update_sehra(
    sehra_id: str,
    body: UpdateSehraRequest,
    user: dict = Depends(get_current_user),
):
    """Partially update a SEHRA (executive summary, recommendations, status)."""
    if body.status is not None:
        valid_statuses = {"draft", "reviewed", "published"}
        if body.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {valid_statuses}",
            )
    sehra = get_sehra(sehra_id)
    if not sehra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SEHRA '{sehra_id}' not found.",
        )
    update_sehra_fields(
        sehra_id,
        executive_summary=body.executive_summary,
        recommendations=body.recommendations,
        status=body.status,
    )
    updated_fields = [
        f for f in ("executive_summary", "recommendations", "status")
        if getattr(body, f) is not None
    ]
    logger.info(
        "User '%s' updated SEHRA '%s' fields: %s",
        user["sub"], sehra_id, ", ".join(updated_fields),
    )
    updated = get_sehra(sehra_id)
    return SEHRADetail(**updated)


@router.patch("/sehras/{sehra_id}/status", response_model=SEHRADetail)
def change_status(
    sehra_id: str,
    body: UpdateStatusRequest,
    user: dict = Depends(get_current_user),
):
    """Update SEHRA status (draft/reviewed/published)."""
    valid_statuses = {"draft", "reviewed", "published"}
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )
    sehra = get_sehra(sehra_id)
    if not sehra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SEHRA '{sehra_id}' not found.",
        )
    update_sehra_status(sehra_id, body.status)
    logger.info(
        "User '%s' updated SEHRA '%s' status to '%s'",
        user["sub"], sehra_id, body.status,
    )
    updated = get_sehra(sehra_id)
    return SEHRADetail(**updated)


@router.get("/sehras/{sehra_id}/components", response_model=list[ComponentAnalysisSchema])
def get_components(sehra_id: str, response: Response, user: dict = Depends(get_current_user)):
    """Get all component analyses for a SEHRA."""
    response.headers["Cache-Control"] = "private, max-age=5, stale-while-revalidate=15"
    sehra = get_sehra(sehra_id)
    if not sehra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SEHRA '{sehra_id}' not found.",
        )
    analyses = get_component_analyses(sehra_id)
    result = []
    for ca in analyses:
        entries = [
            QualitativeEntrySchema(**e)
            for e in ca.get("qualitative_entries", [])
        ]
        sections = {}
        for sec_type, sec_data in ca.get("report_sections", {}).items():
            sections[sec_type] = ReportSectionSchema(**sec_data)

        result.append(ComponentAnalysisSchema(
            id=ca["id"],
            component=ca["component"],
            enabler_count=ca["enabler_count"],
            barrier_count=ca["barrier_count"],
            items=ca.get("items", []),
            qualitative_entries=entries,
            report_sections=sections,
        ))
    return result


@router.get("/sehras/{sehra_id}/summary")
def get_summary(sehra_id: str, user: dict = Depends(get_current_user)):
    """Get executive summary and recommendations for a SEHRA."""
    sehra = get_sehra(sehra_id)
    if not sehra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SEHRA '{sehra_id}' not found.",
        )
    return get_executive_summary(sehra_id)


@router.post("/sehras/{sehra_id}/batch-approve", response_model=BatchApproveResponse)
def batch_approve(
    sehra_id: str,
    body: BatchApproveRequest,
    user: dict = Depends(get_current_user),
):
    """Batch approve qualitative entries above a confidence threshold."""
    sehra = get_sehra(sehra_id)
    if not sehra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SEHRA '{sehra_id}' not found.",
        )
    count = batch_approve_entries(sehra_id, body.confidence_threshold)
    logger.info(
        "User '%s' batch approved %d entries for SEHRA '%s' (threshold=%.2f)",
        user["sub"], count, sehra_id, body.confidence_threshold,
    )
    return BatchApproveResponse(approved_count=count)


@router.patch("/entries/{entry_id}")
def update_entry(
    entry_id: str,
    body: UpdateEntryRequest,
    user: dict = Depends(get_current_user),
):
    """Update a qualitative entry (theme and/or classification)."""
    update_qualitative_entry(
        entry_id,
        theme=body.theme,
        classification=body.classification,
    )
    logger.info("User '%s' updated entry '%s'", user["sub"], entry_id)
    return {"status": "updated", "id": entry_id}


@router.patch("/sections/{section_id}")
def update_section(
    section_id: str,
    body: UpdateSectionRequest,
    user: dict = Depends(get_current_user),
):
    """Update a report section content."""
    update_report_section(section_id, body.content)
    logger.info("User '%s' updated section '%s'", user["sub"], section_id)
    return {"status": "updated", "id": section_id}
