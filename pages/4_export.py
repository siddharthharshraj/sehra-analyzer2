"""Page 4: Unified Export & Share — download reports and create share links."""

import logging
import streamlit as st
import bcrypt

from core.db import (
    list_sehras, get_component_analyses, get_executive_summary,
    create_shared_report, list_shared_reports, revoke_shared_report,
    get_report_views,
)
from core.report_gen import generate_report
from core.report_html import generate_html_report
from core.report_xlsx import generate_xlsx_report
from core.share_utils import get_share_url
from core.codebook import COMPONENT_NAMES
from core.ui_theme import page_header, section_header, export_card

logger = logging.getLogger("sehra.export")

page_header("Export & Share", "Download reports and create secure share links")

# Select SEHRA
sehras = list_sehras()
if not sehras:
    st.info("No SEHRA analyses found. Upload a PDF or collect data first.")
    st.stop()

sehra_options = {}
for s in sehras:
    label = f"{s['country']} - {s['district']} ({s['status']})"
    sehra_options[label] = s

selected_label = st.selectbox("Select SEHRA", options=list(sehra_options.keys()))
selected_sehra = sehra_options[selected_label]

analyses = get_component_analyses(selected_sehra["id"])
if not analyses:
    st.warning("No analysis data found for this SEHRA.")
    st.stop()

exec_data = get_executive_summary(selected_sehra["id"])
header_info = {
    "country": selected_sehra["country"],
    "district": selected_sehra["district"],
    "assessment_date": selected_sehra.get("assessment_date", ""),
}

# --- Export Section ---
section_header("Export Report", "Generate reports in multiple formats")

col1, col2, col3, col4 = st.columns(4)

with col1:
    with st.container(border=True):
        export_card("DOCX", "Word document with charts", "W")
    if st.button("Generate", key="gen_docx", use_container_width=True):
        with st.spinner("Generating DOCX..."):
            docx_buf = generate_report(
                selected_sehra, analyses, header_info,
                executive_summary=exec_data.get("executive_summary", ""),
                recommendations=exec_data.get("recommendations", ""),
            )
            filename = f"SEHRA_{selected_sehra['country']}_{selected_sehra['district']}.docx"
            st.download_button(
                "⬇️ Download DOCX", data=docx_buf, file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )

with col2:
    with st.container(border=True):
        export_card("XLSX", "Spreadsheet with data tables", "X")
    if st.button("Generate", key="gen_xlsx", use_container_width=True):
        with st.spinner("Generating XLSX..."):
            xlsx_buf = generate_xlsx_report(
                analyses, header_info,
                executive_summary=exec_data.get("executive_summary", ""),
                recommendations=exec_data.get("recommendations", ""),
            )
            filename = f"SEHRA_{selected_sehra['country']}_{selected_sehra['district']}.xlsx"
            st.download_button(
                "⬇️ Download XLSX", data=xlsx_buf, file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

with col3:
    with st.container(border=True):
        export_card("PDF", "Print-ready document", "P")
    if st.button("Generate", key="gen_pdf", use_container_width=True):
        with st.spinner("Generating PDF..."):
            try:
                html = generate_html_report(
                    analyses, header_info,
                    executive_summary=exec_data.get("executive_summary", ""),
                    recommendations=exec_data.get("recommendations", ""),
                )
                from core.report_pdf import generate_pdf_report
                pdf_buf = generate_pdf_report(html)
                filename = f"SEHRA_{selected_sehra['country']}_{selected_sehra['district']}.pdf"
                st.download_button(
                    "⬇️ Download PDF", data=pdf_buf, file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                )
            except RuntimeError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"PDF generation failed: {e}")

with col4:
    with st.container(border=True):
        export_card("HTML", "Web-viewable report", "H")
    if st.button("Generate", key="gen_html", use_container_width=True):
        with st.spinner("Generating HTML..."):
            html = generate_html_report(
                analyses, header_info,
                executive_summary=exec_data.get("executive_summary", ""),
                recommendations=exec_data.get("recommendations", ""),
            )
            filename = f"SEHRA_{selected_sehra['country']}_{selected_sehra['district']}.html"
            st.download_button(
                "⬇️ Download HTML", data=html, file_name=filename,
                mime="text/html",
                use_container_width=True,
            )

# Report preview
with st.expander("Report Preview"):
    st.markdown(f"**Country:** {selected_sehra['country']}")
    st.markdown(f"**District:** {selected_sehra['district']}")
    st.markdown(f"**Components:** {len(analyses)}")

    if exec_data.get("executive_summary"):
        st.markdown("**Executive Summary:**")
        st.markdown(exec_data["executive_summary"][:500] + "...")

    for analysis in sorted(analyses,
                           key=lambda a: COMPONENT_NAMES.get(a["component"], a["component"])):
        comp_name = COMPONENT_NAMES.get(analysis["component"], analysis["component"])
        entries = analysis.get("qualitative_entries", [])
        st.markdown(
            f"- **{comp_name}**: {analysis['enabler_count']} enablers, "
            f"{analysis['barrier_count']} barriers, {len(entries)} remarks"
        )

# --- Share Section ---
st.divider()
section_header("Share Report", "Create password-protected share links")

col_pass, col_expiry = st.columns(2)
with col_pass:
    passcode = st.text_input("Set Passcode", type="password",
                              help="Recipients need this to view the report")
with col_expiry:
    expiry_options = {"7 days": 7, "30 days": 30, "90 days": 90, "Never": None}
    expiry_label = st.selectbox("Expiry", options=list(expiry_options.keys()), index=1)
    expiry_days = expiry_options[expiry_label]

if st.button("Generate Share Link", type="primary", use_container_width=True):
    if not passcode:
        st.warning("Please set a passcode.")
    elif len(passcode) < 4:
        st.warning("Passcode must be at least 4 characters.")
    else:
        with st.spinner("Generating report snapshot..."):
            html = generate_html_report(
                analyses, header_info,
                executive_summary=exec_data.get("executive_summary", ""),
                recommendations=exec_data.get("recommendations", ""),
            )
            passcode_hash = bcrypt.hashpw(
                passcode.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            username = st.session_state.get("username", "unknown")
            token = create_shared_report(
                sehra_id=selected_sehra["id"],
                passcode_hash=passcode_hash,
                created_by=username,
                expires_days=expiry_days,
                cached_html=html,
            )
            share_url = get_share_url(token)
            st.success("Share link created!")
            st.code(share_url, language=None)
            st.info("Share this URL and passcode with the recipient.")

# Existing links
shared = list_shared_reports(selected_sehra["id"])
if shared:
    st.markdown("**Existing Share Links:**")
    for sr in shared:
        token_masked = sr["share_token"][:8] + "..."
        status_text = "Active" if sr["is_active"] else "Revoked"
        status_color = "green" if sr["is_active"] else "red"

        with st.container(border=True):
            sc1, sc2, sc3, sc4 = st.columns([2, 2, 1, 1])
            with sc1:
                st.markdown(f"**Token:** `{token_masked}`")
                st.caption(f"By: {sr['created_by']}")
            with sc2:
                st.caption(f"Created: {sr['created_at'][:10] if sr['created_at'] else 'N/A'}")
                exp = sr['expires_at'][:10] if sr['expires_at'] else 'Never'
                st.caption(f"Expires: {exp}")
            with sc3:
                st.metric("Views", sr["view_count"])
            with sc4:
                st.markdown(f":{status_color}[{status_text}]")
                if sr["is_active"]:
                    if st.button("Revoke", key=f"revoke_{sr['id']}"):
                        revoke_shared_report(sr["share_token"])
                        st.success("Link revoked!")
                        st.rerun()

            with st.expander("Audit Log"):
                views = get_report_views(sr["id"])
                if views:
                    for v in views:
                        icon = "✅" if v["passcode_correct"] else "❌"
                        st.caption(
                            f"{icon} {v['viewed_at'][:19] if v['viewed_at'] else 'N/A'} | "
                            f"IP: {v['viewer_ip'] or 'unknown'}"
                        )
                else:
                    st.caption("No views yet.")
