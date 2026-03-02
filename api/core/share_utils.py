"""Share URL builder and public report view handler.

Handles the public-facing share link flow:
1. Look up token
2. Check expiry/active status
3. Rate limit failed attempts
4. Show passcode form
5. Verify passcode
6. Log view
7. Render cached HTML
"""

import os
import logging
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from core.db import (
    get_shared_report_by_token,
    verify_share_passcode,
    log_report_view,
    count_failed_attempts,
)
from core.exceptions import ShareError

logger = logging.getLogger("sehra.share")

MAX_FAILED_ATTEMPTS = 5
RATE_LIMIT_MINUTES = 60


def get_share_url(token: str) -> str:
    """Build a share URL using APP_URL env var."""
    base_url = os.environ.get("APP_URL", "http://localhost:8501")
    return f"{base_url}/?token={token}"


def get_viewer_ip() -> str:
    """Get viewer IP from Streamlit context headers."""
    try:
        headers = st.context.headers
        # Check common proxy headers
        for header in ["x-forwarded-for", "x-real-ip", "cf-connecting-ip"]:
            ip = headers.get(header, "")
            if ip:
                return ip.split(",")[0].strip()
        return ""
    except Exception:
        return ""


def get_viewer_user_agent() -> str:
    """Get viewer user agent from Streamlit context headers."""
    try:
        return st.context.headers.get("user-agent", "")[:200]
    except Exception:
        return ""


def render_public_report_view(token: str):
    """Full public report view flow.

    Called from app.py when ?token=X is detected.
    """
    # Note: st.set_page_config() is already called in app.py before this runs

    # Look up report
    report = get_shared_report_by_token(token)
    if not report:
        st.error("This share link is invalid or has been removed.")
        return

    # Check active
    if not report["is_active"]:
        st.error("This share link has been deactivated.")
        return

    # Check expiry
    if report["expires_at"]:
        expires = datetime.fromisoformat(report["expires_at"])
        if datetime.utcnow() > expires:
            st.error("This share link has expired.")
            return

    # Rate limiting
    failed = count_failed_attempts(report["id"], RATE_LIMIT_MINUTES)
    if failed >= MAX_FAILED_ATTEMPTS:
        st.error("Too many failed attempts. Please try again later.")
        log_report_view(
            report["id"],
            viewer_ip=get_viewer_ip(),
            viewer_user_agent=get_viewer_user_agent(),
            passcode_correct=False,
        )
        return

    # Check if already authenticated in this session
    session_key = f"share_auth_{token}"
    if st.session_state.get(session_key):
        _render_report(report)
        return

    # Show passcode form
    st.title("SEHRA Analysis Report")
    st.markdown("This report is protected. Please enter the passcode to view.")

    passcode = st.text_input("Passcode", type="password", key=f"passcode_{token}")

    if st.button("View Report", type="primary"):
        if not passcode:
            st.warning("Please enter a passcode.")
            return

        if verify_share_passcode(token, passcode):
            # Success
            log_report_view(
                report["id"],
                viewer_ip=get_viewer_ip(),
                viewer_user_agent=get_viewer_user_agent(),
                passcode_correct=True,
            )
            st.session_state[session_key] = True
            logger.info("Share report viewed: token=%s...", token[:8])
            st.rerun()
        else:
            # Failed
            log_report_view(
                report["id"],
                viewer_ip=get_viewer_ip(),
                viewer_user_agent=get_viewer_user_agent(),
                passcode_correct=False,
            )
            remaining = MAX_FAILED_ATTEMPTS - failed - 1
            st.error(f"Incorrect passcode. {remaining} attempts remaining.")


def _render_report(report: dict):
    """Render the cached HTML report."""
    html = report.get("cached_html", "")
    if not html:
        st.error("Report content is not available.")
        return

    st.markdown(
        "<div style='text-align: center; padding: 10px; color: #666;'>"
        "SEHRA Analysis Report | Shared view</div>",
        unsafe_allow_html=True,
    )
    components.html(html, height=800, scrolling=True)
