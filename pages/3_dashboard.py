"""Page 3: Unified Dashboard with KPIs, charts, review, and AI chat."""

import json
import logging
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from core.db import (
    list_sehras, get_component_analyses, get_executive_summary,
    update_qualitative_entry, update_report_section,
    update_sehra_status, batch_approve_entries,
)
from core.codebook import COMPONENT_NAMES
from core.charts import (
    create_radar_chart, create_theme_heatmap,
    create_enabler_barrier_bar,
    build_theme_data_from_analyses,
    COMPONENT_ORDER, TEAL, RED,
)
from core.ui_theme import (
    page_header, kpi_card, section_header, status_badge,
    apply_plotly_theme, GRAY_600,
)

logger = logging.getLogger("sehra.dashboard")

THEMES = [
    "Institutional Structure and Stakeholders",
    "Operationalization Strategies",
    "Coordination and Integration",
    "Funding",
    "Local Capacity and Service Delivery",
    "Accessibility and Inclusivity",
    "Cost, Availability and Affordability",
    "Data Considerations",
    "Sociocultural Factors and Compliance",
    "Services at Higher Levels of Health System",
    "Provision of Eyeglasses",
]

CLASSIFICATIONS = ["enabler", "barrier", "strength", "weakness"]

page_header("Dashboard", "Review analysis results, charts, and AI insights")

# Select SEHRA
sehras = list_sehras()
if not sehras:
    st.info("No SEHRA analyses found. Upload a PDF or collect data first.")
    st.stop()

sehra_options = {}
for s in sehras:
    label = f"{s['country']} - {s['district']}"
    sehra_options[label] = s

col_sel, col_status = st.columns([3, 1])
with col_sel:
    selected_label = st.selectbox("Select SEHRA", options=list(sehra_options.keys()),
                                   label_visibility="collapsed")
with col_status:
    selected_sehra = sehra_options[selected_label]
    status = selected_sehra["status"]
    status_badge(status)

selected_id = selected_sehra["id"]
analyses = get_component_analyses(selected_id)

if not analyses:
    st.warning("No analysis data found for this SEHRA.")
    st.stop()

# --- KPI Cards (5-second rule) ---
total_enablers = sum(a.get("enabler_count", 0) for a in analyses)
total_barriers = sum(a.get("barrier_count", 0) for a in analyses)
total_remarks = sum(len(a.get("qualitative_entries", [])) for a in analyses)
grand_total = total_enablers + total_barriers
readiness_score = round(total_enablers / grand_total * 100) if grand_total > 0 else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    kpi_card(total_enablers, "Enablers", color=TEAL)

with kpi2:
    kpi_card(total_barriers, "Barriers", color=RED)

with kpi3:
    readiness_color = TEAL if readiness_score >= 50 else RED
    kpi_card(readiness_score, "Readiness", color=readiness_color, suffix="%")

with kpi4:
    kpi_card(total_remarks, "Remarks", color=GRAY_600)

st.markdown("")  # spacing

# --- Executive Summary ---
exec_data = get_executive_summary(selected_id)
if exec_data.get("executive_summary"):
    with st.expander("Executive Summary", expanded=False):
        st.markdown(exec_data["executive_summary"])

# --- Charts Row ---
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    comp_scores = {}
    for a in analyses:
        comp_scores[a["component"]] = {
            "enabler_count": a.get("enabler_count", 0),
            "barrier_count": a.get("barrier_count", 0),
        }
    radar_fig, _ = create_radar_chart(comp_scores)
    radar_fig.update_layout(height=380, margin=dict(t=40, b=20))
    apply_plotly_theme(radar_fig)
    st.plotly_chart(radar_fig, use_container_width=True)

with chart_col2:
    bar_data = []
    for a in analyses:
        comp = a["component"]
        if comp in COMPONENT_ORDER:
            bar_data.append({
                "name": COMPONENT_NAMES.get(comp, comp),
                "enabler_count": a.get("enabler_count", 0),
                "barrier_count": a.get("barrier_count", 0),
            })
    if bar_data:
        bar_fig, _ = create_enabler_barrier_bar(bar_data)
        bar_fig.update_layout(height=380, margin=dict(t=40, b=60))
        apply_plotly_theme(bar_fig)
        st.plotly_chart(bar_fig, use_container_width=True)

# --- Component Tabs ---
st.divider()
section_header("Components", "Detailed breakdown by SEHRA component")

comp_lookup = {a["component"]: a for a in analyses}
visible_comps = [c for c in COMPONENT_ORDER if c in comp_lookup]
tab_names = [COMPONENT_NAMES.get(c, c) for c in visible_comps]
tabs = st.tabs(tab_names)

for tab, comp_key in zip(tabs, visible_comps):
    with tab:
        analysis = comp_lookup[comp_key]
        entries = analysis.get("qualitative_entries", [])

        # Component metrics
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Enablers", analysis["enabler_count"])
        with c2:
            st.metric("Barriers", analysis["barrier_count"])

        # Enablers table
        enabler_entries = [e for e in entries if e.get("classification") in ("enabler", "strength")]
        barrier_entries = [e for e in entries if e.get("classification") in ("barrier", "weakness")]
        strength_entries = [e for e in entries if e.get("classification") == "strength"]
        weakness_entries = [e for e in entries if e.get("classification") == "weakness"]

        if enabler_entries:
            with st.expander(f"Enablers ({len(enabler_entries)})", expanded=False):
                df_en = pd.DataFrame([
                    {"Theme": e["theme"], "Remark": e["remark_text"][:200],
                     "Confidence": f"{e['confidence']:.0%}"}
                    for e in enabler_entries
                ])
                st.dataframe(df_en, use_container_width=True, hide_index=True)

        if barrier_entries:
            with st.expander(f"Barriers ({len(barrier_entries)})", expanded=False):
                df_ba = pd.DataFrame([
                    {"Theme": e["theme"], "Remark": e["remark_text"][:200],
                     "Confidence": f"{e['confidence']:.0%}"}
                    for e in barrier_entries
                ])
                st.dataframe(df_ba, use_container_width=True, hide_index=True)

        # Strengths & Weaknesses as separate views
        if strength_entries:
            with st.expander(f"Strengths ({len(strength_entries)})", expanded=False):
                for e in strength_entries:
                    st.markdown(f"- **{e['theme']}**: {e['remark_text'][:200]}")

        if weakness_entries:
            with st.expander(f"Weaknesses ({len(weakness_entries)})", expanded=False):
                for e in weakness_entries:
                    st.markdown(f"- **{e['theme']}**: {e['remark_text'][:200]}")

        # Summaries & Action Points
        sections = analysis.get("report_sections", {})
        if sections:
            with st.expander("Summaries & Action Points", expanded=False):
                for section_type, section_data in sections.items():
                    if section_data.get("content"):
                        label = section_type.replace("_", " ").title()
                        st.markdown(f"**{label}:**")
                        st.markdown(section_data["content"])
                        st.markdown("")

        # Edit Classifications (review functionality)
        with st.expander("Edit Classifications", expanded=False):
            if entries:
                st.caption("Edit theme and classification. Changes save automatically.")
                for i, entry in enumerate(entries):
                    with st.container(border=True):
                        st.markdown(f"**{entry.get('item_id', '')}**: {entry['remark_text'][:150]}...")
                        ec1, ec2, ec3 = st.columns([2, 2, 1])
                        with ec1:
                            current_theme = entry["theme"]
                            theme_idx = THEMES.index(current_theme) if current_theme in THEMES else 0
                            new_theme = st.selectbox(
                                "Theme", options=THEMES, index=theme_idx,
                                key=f"dash_theme_{comp_key}_{entry['id']}",
                                label_visibility="collapsed",
                            )
                        with ec2:
                            current_cls = entry["classification"]
                            cls_idx = CLASSIFICATIONS.index(current_cls) if current_cls in CLASSIFICATIONS else 0
                            new_cls = st.selectbox(
                                "Classification", options=CLASSIFICATIONS, index=cls_idx,
                                key=f"dash_cls_{comp_key}_{entry['id']}",
                                label_visibility="collapsed",
                            )
                        with ec3:
                            conf = entry.get("confidence", 0)
                            color = "green" if conf > 0.8 else "orange" if conf > 0.5 else "red"
                            st.markdown(f":{color}[{conf:.0%}]")

                        if new_theme != entry["theme"] or new_cls != entry["classification"]:
                            update_qualitative_entry(entry["id"], theme=new_theme, classification=new_cls)
                            st.toast("Updated", icon="✅")

            # Editable report sections
            if sections:
                st.markdown("---")
                st.markdown("**Edit Summaries:**")
                for section_type, section_data in sections.items():
                    label = section_type.replace("_", " ").title()
                    new_content = st.text_area(
                        label,
                        value=section_data.get("content", ""),
                        height=120,
                        key=f"dash_section_{comp_key}_{section_data['id']}",
                    )
                    if new_content != section_data.get("content", ""):
                        update_report_section(section_data["id"], new_content)
                        st.toast(f"Updated {label}", icon="✅")

# --- AI Assistant ---
st.divider()
section_header("AI Assistant", "Ask questions about this SEHRA analysis")

# Initialize chat history
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Display chat history
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("chart"):
            fig = go.Figure(msg["chart"])
            st.plotly_chart(fig, use_container_width=True)

# Chat input
if prompt := st.chat_input("Ask about this SEHRA..."):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                from core.chat_agent import chat_query
                response = chat_query(
                    prompt, analyses,
                    executive_summary=exec_data.get("executive_summary", ""),
                )
                st.markdown(response.text)
                assistant_msg = {"role": "assistant", "content": response.text}

                if response.chart:
                    fig = go.Figure(response.chart)
                    st.plotly_chart(fig, use_container_width=True)
                    assistant_msg["chart"] = response.chart

                st.session_state.chat_messages.append(assistant_msg)
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)[:200]}"
                st.markdown(error_msg)
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": error_msg}
                )

# --- Review Controls ---
st.divider()
section_header("Review Controls")
col_review1, col_review2, col_review3 = st.columns(3)

with col_review1:
    batch_thresh = st.number_input(
        "Batch approve above confidence",
        min_value=0.5, max_value=1.0, value=0.85, step=0.05, format="%.2f",
    )
    if st.button("Batch Approve"):
        count = batch_approve_entries(selected_id, batch_thresh)
        st.success(f"Approved {count} entries above {batch_thresh:.0%}")
        st.rerun()

with col_review2:
    if st.button("Mark as Reviewed", type="primary", use_container_width=True):
        update_sehra_status(selected_id, "reviewed")
        st.success("Marked as reviewed!")
        st.rerun()

with col_review3:
    if st.button("Mark as Published", use_container_width=True):
        update_sehra_status(selected_id, "published")
        st.success("Marked as published!")
        st.rerun()
