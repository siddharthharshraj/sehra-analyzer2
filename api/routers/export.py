"""Export endpoints for downloading reports in various formats."""

import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from api.deps import get_current_user
from api.core import db

logger = logging.getLogger("sehra.routers.export")
router = APIRouter()

IST = timezone(timedelta(hours=5, minutes=30))


def _now_ist() -> str:
    """Return current time formatted in IST."""
    return datetime.now(IST).strftime("%d %b %Y, %I:%M %p")


def _get_ip(request: Request) -> str:
    """Extract client IP from request (supports proxies)."""
    return (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.headers.get("x-real-ip", "")
        or (request.client.host if request.client else "")
    )


def _get_sehra_data(sehra_id: str):
    """Common helper to load SEHRA data for reports."""
    sehra = db.get_sehra(sehra_id)
    if not sehra:
        raise HTTPException(status_code=404, detail="SEHRA not found")

    components = db.get_component_analyses(sehra_id)
    summary = db.get_executive_summary(sehra_id)

    header_info = {
        "country": sehra.get("country", ""),
        "district": sehra.get("district", ""),
        "province": sehra.get("province", ""),
        "assessment_date": sehra.get("assessment_date", ""),
    }

    return sehra, components, header_info, summary


@router.get("/export/{sehra_id}/docx")
def export_docx(sehra_id: str, request: Request, user: dict = Depends(get_current_user)):
    # Lazy import — matplotlib + python-docx only loaded when DOCX is actually requested
    from api.core.report_gen import generate_report

    sehra, components, header_info, summary = _get_sehra_data(sehra_id)
    buf = generate_report(
        sehra, components, header_info,
        executive_summary=summary.get("executive_summary", ""),
        recommendations=summary.get("recommendations", ""),
        generated_at_ist=_now_ist(),
        requester_ip=_get_ip(request),
        exported_by=user.get("sub", ""),
        country=sehra.get("country", ""),
    )
    filename = f"SEHRA_{sehra.get('country', 'report')}_{sehra_id[:8]}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/{sehra_id}/xlsx")
def export_xlsx(sehra_id: str, request: Request, user: dict = Depends(get_current_user)):
    # Lazy import — openpyxl only loaded when XLSX is actually requested
    from api.core.report_xlsx import generate_xlsx_report

    sehra, components, header_info, summary = _get_sehra_data(sehra_id)
    buf = generate_xlsx_report(
        components, header_info,
        executive_summary=summary.get("executive_summary", ""),
        recommendations=summary.get("recommendations", ""),
        generated_at_ist=_now_ist(),
        requester_ip=_get_ip(request),
        exported_by=user.get("sub", ""),
        country=sehra.get("country", ""),
    )
    filename = f"SEHRA_{sehra.get('country', 'report')}_{sehra_id[:8]}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/{sehra_id}/html")
def export_html(sehra_id: str, request: Request, user: dict = Depends(get_current_user)):
    from api.core.report_html import generate_html_report

    sehra, components, header_info, summary = _get_sehra_data(sehra_id)
    html = generate_html_report(
        components, header_info,
        executive_summary=summary.get("executive_summary", ""),
        recommendations=summary.get("recommendations", ""),
        generated_at_ist=_now_ist(),
        requester_ip=_get_ip(request),
        exported_by=user.get("sub", ""),
        country=sehra.get("country", ""),
    )
    filename = f"SEHRA_{sehra.get('country', 'report')}_{sehra_id[:8]}.html"
    return StreamingResponse(
        iter([html.encode("utf-8")]),
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/{sehra_id}/pdf")
def export_pdf(sehra_id: str, request: Request, user: dict = Depends(get_current_user)):
    # Lazy import — weasyprint only loaded when PDF is actually requested
    from api.core.report_html import generate_html_report
    from api.core.report_pdf import generate_pdf_report

    sehra, components, header_info, summary = _get_sehra_data(sehra_id)
    html = generate_html_report(
        components, header_info,
        executive_summary=summary.get("executive_summary", ""),
        recommendations=summary.get("recommendations", ""),
        generated_at_ist=_now_ist(),
        requester_ip=_get_ip(request),
        exported_by=user.get("sub", ""),
        static_charts=True,
        country=sehra.get("country", ""),
    )
    buf = generate_pdf_report(html)
    filename = f"SEHRA_{sehra.get('country', 'report')}_{sehra_id[:8]}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
