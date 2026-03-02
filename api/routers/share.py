"""Share link management and public report access."""

import logging
from datetime import datetime, timezone, timedelta

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request

from api.deps import get_current_user
from api.schemas import (
    ShareCreateRequest, ShareLinkSchema,
    PublicShareResponse, VerifyPasscodeRequest, VerifyPasscodeResponse,
)
from api.core import db
from api.core.report_html import generate_html_report

IST = timezone(timedelta(hours=5, minutes=30))

logger = logging.getLogger("sehra.routers.share")
router = APIRouter()


@router.post("/shares", response_model=ShareLinkSchema)
def create_share(req: ShareCreateRequest, request: Request, user: dict = Depends(get_current_user)):
    """Create a new share link for a SEHRA report."""
    sehra = db.get_sehra(req.sehra_id)
    if not sehra:
        raise HTTPException(status_code=404, detail="SEHRA not found")

    # Generate cached HTML
    components = db.get_component_analyses(req.sehra_id)
    summary = db.get_executive_summary(req.sehra_id)
    header_info = {
        "country": sehra.get("country", ""),
        "district": sehra.get("district", ""),
        "assessment_date": sehra.get("assessment_date", ""),
    }
    creator_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.headers.get("x-real-ip", "")
        or (request.client.host if request.client else "")
    )
    cached_html = generate_html_report(
        components, header_info,
        executive_summary=summary.get("executive_summary", ""),
        recommendations=summary.get("recommendations", ""),
        generated_at_ist=datetime.now(IST).strftime("%d %b %Y, %I:%M %p"),
        requester_ip=creator_ip,
        exported_by=user.get("sub", ""),
        static_charts=True,
    )

    # Hash passcode
    passcode_hash = bcrypt.hashpw(
        req.passcode.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    token = db.create_shared_report(
        sehra_id=req.sehra_id,
        passcode_hash=passcode_hash,
        created_by=user["sub"],
        expires_days=req.expires_days,
        cached_html=cached_html,
    )

    # Return the created share link
    shares = db.list_shared_reports(req.sehra_id)
    for s in shares:
        if s["share_token"] == token:
            return s

    return ShareLinkSchema(id="", share_token=token, created_by=user["sub"])


@router.get("/shares/{sehra_id}", response_model=list[ShareLinkSchema])
def list_shares(sehra_id: str, user: dict = Depends(get_current_user)):
    return db.list_shared_reports(sehra_id)


@router.delete("/shares/{token}", status_code=204)
def revoke_share(token: str, user: dict = Depends(get_current_user)):
    db.revoke_shared_report(token)


@router.get("/shares/{token}/audit")
def get_audit(token: str, user: dict = Depends(get_current_user)):
    report = db.get_shared_report_by_token(token)
    if not report:
        raise HTTPException(status_code=404, detail="Share link not found")
    return db.get_report_views(report["id"])


# --- Public endpoints (no auth) ---

@router.get("/public/share/{token}", response_model=PublicShareResponse)
def check_share(token: str):
    """Check if a share link is valid (no auth required)."""
    report = db.get_shared_report_by_token(token)
    if not report:
        return PublicShareResponse(valid=False)

    if not report["is_active"]:
        return PublicShareResponse(valid=False)

    expired = False
    if report["expires_at"]:
        expires = datetime.fromisoformat(report["expires_at"])
        if datetime.utcnow() > expires:
            expired = True

    return PublicShareResponse(valid=True, expired=expired, needs_passcode=True)


@router.post("/public/share/{token}/verify", response_model=VerifyPasscodeResponse)
def verify_passcode(token: str, req: VerifyPasscodeRequest, request: Request):
    """Verify passcode and return HTML report (no auth required)."""
    report = db.get_shared_report_by_token(token)
    if not report:
        raise HTTPException(status_code=404, detail="Share link not found")

    if not report["is_active"]:
        raise HTTPException(status_code=410, detail="Share link deactivated")

    if report["expires_at"]:
        expires = datetime.fromisoformat(report["expires_at"])
        if datetime.utcnow() > expires:
            raise HTTPException(status_code=410, detail="Share link expired")

    # Rate limiting
    failed = db.count_failed_attempts(report["id"], 60)
    if failed >= 5:
        raise HTTPException(status_code=429, detail="Too many failed attempts")

    # Get viewer info
    viewer_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "")
    viewer_ua = request.headers.get("user-agent", "")[:200]

    if db.verify_share_passcode(token, req.passcode):
        db.log_report_view(report["id"], viewer_ip=viewer_ip, viewer_user_agent=viewer_ua, passcode_correct=True)
        return VerifyPasscodeResponse(success=True, html=report.get("cached_html", ""))
    else:
        db.log_report_view(report["id"], viewer_ip=viewer_ip, viewer_user_agent=viewer_ua, passcode_correct=False)
        return VerifyPasscodeResponse(success=False)
