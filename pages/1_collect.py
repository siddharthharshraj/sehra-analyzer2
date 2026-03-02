"""Page 1: Web form for field workers to enter SEHRA data directly."""

import json
import logging
from pathlib import Path
from datetime import date

import streamlit as st

from core.ui_theme import page_header, section_header, step_indicator
from core.codebook import load_codebook, score_all_items, COMPONENT_NAMES
from core.ai_engine import analyze_full_sehra, generate_executive_summary, generate_recommendations
from core.db import (
    create_sehra, save_component_analysis,
    save_qualitative_entries, save_report_section,
    save_executive_summary as save_exec_summary,
    save_form_draft, get_form_draft, delete_form_draft,
)

logger = logging.getLogger("sehra.collect")

# Section definitions matching SEHRA structure
SECTIONS = [
    {"key": "header", "title": "Header"},
    {"key": "context", "title": "Context"},
    {"key": "policy", "title": "Policy"},
    {"key": "service_delivery", "title": "Service Delivery"},
    {"key": "human_resources", "title": "HR"},
    {"key": "supply_chain", "title": "Supply Chain"},
    {"key": "barriers", "title": "Barriers"},
]


def _load_codebook_items_by_section() -> dict:
    """Load codebook and group items by section."""
    codebook = load_codebook()
    by_section = {}
    for item in codebook["items"]:
        section = item["section"]
        if section not in by_section:
            by_section[section] = []
        by_section[section].append(item)
    return by_section


def _render_header_form(responses: dict) -> dict:
    """Render the header information form fields."""
    result = {}
    col1, col2 = st.columns(2)
    with col1:
        result["country"] = st.text_input(
            "Country *", value=responses.get("country", ""),
            key="hdr_country"
        )
        result["province"] = st.text_input(
            "Province / State", value=responses.get("province", ""),
            key="hdr_province"
        )
    with col2:
        result["district"] = st.text_input(
            "District *", value=responses.get("district", ""),
            key="hdr_district"
        )
        result["assessment_date"] = st.date_input(
            "Assessment Date",
            value=date.today(),
            key="hdr_date"
        )
    result["assessor_name"] = st.text_input(
        "Assessor Name", value=responses.get("assessor_name", ""),
        key="hdr_assessor"
    )
    return result


def _detect_grid_groups(items: list[dict]) -> list:
    """Detect groups of items that share a common pattern for grid display.

    Returns list of (group_items, base_question, column_labels) tuples,
    plus standalone items as (item, None, None).
    """
    import re
    result = []
    used = set()

    for i, item in enumerate(items):
        if i in used:
            continue
        if item["type"] != "categorical_text":
            result.append(([item], None, None))
            continue

        # Look for consecutive items with similar questions
        # e.g. "X at School nurse level", "X at Community health level"
        q = item["question"]
        # Try to find a sector/level suffix pattern
        patterns = [
            r'(.+?)\s+(at the |at |for the |for )?(\w[\w\s]*?)\s*(level|sector)\s*\??$',
        ]

        base = None
        for pat in patterns:
            m = re.match(pat, q, re.IGNORECASE)
            if m:
                base = m.group(1).strip()
                break

        if not base:
            result.append(([item], None, None))
            continue

        # Find consecutive items with same base
        group = [item]
        used.add(i)
        for j in range(i + 1, min(i + 10, len(items))):
            if j in used:
                continue
            if items[j]["type"] != "categorical_text":
                break
            if items[j]["question"].startswith(base[:20]):
                group.append(items[j])
                used.add(j)

        if len(group) > 1:
            result.append((group, base, None))
        else:
            result.append(([item], None, None))

    return result


def _render_form_section(section_items: list[dict], responses: dict) -> dict:
    """Render form fields for a section based on codebook item types."""
    result = {}

    for item in section_items:
        item_id = item["id"]
        q = item["question"]

        if item["type"] == "numeric":
            val = responses.get(item_id, 0)
            if isinstance(val, str):
                try:
                    val = int(val)
                except (ValueError, TypeError):
                    val = 0
            result[item_id] = st.number_input(
                f"**{item_id}**: {q}",
                min_value=0, value=val, key=f"q_{item_id}_{st.session_state.get('collect_step', 0)}"
            )

        elif item["type"] == "text":
            result[item_id] = st.text_area(
                f"**{item_id}**: {q}",
                value=responses.get(item_id, ""),
                height=80, key=f"q_{item_id}_{st.session_state.get('collect_step', 0)}"
            )

        elif item["type"] == "categorical_text":
            col1, col2 = st.columns([1, 3])
            with col1:
                prev_answer = responses.get(item_id, "")
                options = ["", "Yes", "No"]
                idx = options.index(prev_answer) if prev_answer in options else 0
                result[item_id] = st.selectbox(
                    f"**{item_id}**: {q}",
                    options=options,
                    index=idx,
                    key=f"q_{item_id}_{st.session_state.get('collect_step', 0)}"
                )
            with col2:
                result[f"{item_id}_remark"] = st.text_area(
                    "Remarks",
                    value=responses.get(f"{item_id}_remark", ""),
                    height=68,
                    key=f"q_{item_id}_remark_{st.session_state.get('collect_step', 0)}",
                    label_visibility="collapsed",
                    placeholder="Enter remarks...",
                )

        elif item["type"] == "categorical":
            result[item_id] = st.text_input(
                f"**{item_id}**: {q}",
                value=responses.get(item_id, ""),
                key=f"q_{item_id}_{st.session_state.get('collect_step', 0)}"
            )

        else:
            result[item_id] = st.text_input(
                f"**{item_id}**: {q}",
                value=responses.get(item_id, ""),
                key=f"q_{item_id}_{st.session_state.get('collect_step', 0)}"
            )

    return result


def _form_to_parsed_data(all_responses: dict, header: dict) -> dict:
    """Convert form responses into the same structure as parse_and_enrich() output."""
    codebook = load_codebook()

    # Build item lookup
    item_lookup = {item["id"]: item for item in codebook["items"]}

    components = {}
    for item in codebook["items"]:
        section = item["section"]
        if section == "summary":
            continue
        if section not in components:
            components[section] = {"items": [], "text_field_values": {}, "text": ""}

        item_id = item["id"]

        if item["type"] == "categorical_text":
            answer_val = all_responses.get(item_id, "")
            answer = answer_val.lower() if answer_val in ("Yes", "No") else None
            remark = all_responses.get(f"{item_id}_remark", "")

            components[section]["items"].append({
                "question": item["question"],
                "answer": answer,
                "page_num": 0,
                "remark": remark,
                "item_id": item_id,
                "codebook_question": item["question"],
                "match_confidence": 1.0,
                "component": section,
            })
        elif item["type"] in ("numeric", "text", "categorical"):
            value = all_responses.get(item_id, "")
            remark = str(value) if value else ""
            # These items don't have yes/no scoring
            components[section]["items"].append({
                "question": item["question"],
                "answer": None,
                "page_num": 0,
                "remark": remark,
                "item_id": item_id,
                "codebook_question": item["question"],
                "match_confidence": 1.0,
                "component": section,
            })

    return {
        "header": header,
        "full_text": "",
        "components": components,
    }


def _run_analysis(parsed_data: dict, header: dict):
    """Run the full analysis pipeline on form data."""
    progress = st.progress(0, text="Starting analysis...")
    status = st.status("Analysis Pipeline", expanded=True)

    # Step 1: Score items
    with status:
        st.write("**Step 1/4:** Scoring items (quantitative analysis)...")
    progress.progress(20, text="Scoring items...")

    all_items = []
    for comp_name, comp_data in parsed_data["components"].items():
        for item in comp_data.get("items", []):
            all_items.append({**item, "component": comp_name})

    scores = score_all_items(all_items)

    with status:
        totals = scores["totals"]
        st.write(f"  Total enablers: **{totals['enabler_count']}**")
        st.write(f"  Total barriers: **{totals['barrier_count']}**")

    progress.progress(35, text="Scoring complete")

    # Step 2: AI Analysis
    with status:
        st.write("**Step 2/4:** AI qualitative analysis (this may take 1-2 minutes)...")
    progress.progress(40, text="Running AI analysis...")

    ai_results = analyze_full_sehra(parsed_data)

    with status:
        total_classified = sum(
            len(r.get("classifications", []))
            for r in ai_results.values()
        )
        st.write(f"  Remarks classified: **{total_classified}**")

    progress.progress(70, text="AI analysis complete")

    # Step 3: Save to database
    with status:
        st.write("**Step 3/4:** Saving results...")
    progress.progress(75, text="Saving to database...")

    sehra_id = create_sehra(
        country=header.get("country", "Unknown"),
        district=header.get("district", ""),
        province=header.get("province", ""),
        assessment_date=header.get("assessment_date"),
        pdf_filename="web_form_submission",
        raw_data={"header": header, "source": "web_form"},
    )

    for comp_name in scores["by_component"]:
        comp_scores = scores["by_component"][comp_name]
        comp_ai = ai_results.get(comp_name, {})

        ca_id = save_component_analysis(
            sehra_id=sehra_id,
            component=comp_name,
            enabler_count=comp_scores["enabler_count"],
            barrier_count=comp_scores["barrier_count"],
            items=comp_scores["items"],
        )

        classifications = comp_ai.get("classifications", [])
        if classifications:
            entries = [
                {
                    "remark_text": c.get("remark_text", ""),
                    "item_id": c.get("item_id", ""),
                    "theme": c.get("theme", "Uncategorized"),
                    "classification": c.get("classification", "enabler"),
                    "confidence": c.get("confidence", 0.0),
                }
                for c in classifications
            ]
            save_qualitative_entries(ca_id, entries)

        for summary_type in ["enabler_summary", "barrier_summary"]:
            summaries = comp_ai.get(summary_type, [])
            if summaries:
                content = "\n\n".join(
                    f"**{', '.join(s.get('themes', []))}**: {s.get('summary', '')}"
                    + ("\n\nAction Points:\n" + "\n".join(f"- {ap}" for ap in s.get('action_points', [])))
                    for s in summaries
                )
                save_report_section(ca_id, summary_type, content)

        all_action_points = []
        for summary_type in ["enabler_summary", "barrier_summary"]:
            for s in comp_ai.get(summary_type, []):
                all_action_points.extend(s.get("action_points", []))
        if all_action_points:
            save_report_section(
                ca_id, "action_points",
                "\n".join(f"- {ap}" for ap in all_action_points)
            )

    progress.progress(85, text="Database saved")

    # Step 4: Executive summary
    with status:
        st.write("**Step 4/4:** Generating executive summary & recommendations...")
    progress.progress(90, text="Generating executive summary...")

    try:
        exec_summary = generate_executive_summary(ai_results, header)
        recommendations = generate_recommendations(ai_results, header)
        save_exec_summary(sehra_id, exec_summary, recommendations)
        with status:
            st.write("  Executive summary and recommendations generated")
    except Exception as e:
        logger.warning("Executive summary generation failed: %s", e)
        with status:
            st.write("  ⚠️ Executive summary generation skipped (non-critical)")

    progress.progress(100, text="Analysis complete!")

    with status:
        st.write("**Analysis complete!**")
    status.update(label="Analysis Complete", state="complete")

    return sehra_id, totals


# --- Main Page ---

page_header("Collect SEHRA Data", "Fill out the SEHRA Scoping Module questionnaire step by step.")

username = st.session_state.get("username", "anonymous")

# Load existing draft
if "collect_responses" not in st.session_state:
    draft = get_form_draft(username)
    if draft:
        st.session_state.collect_responses = draft["responses"]
        st.session_state.collect_step = draft["section_progress"]
        st.info(f"Resumed draft from {draft['updated_at'][:10]}.")
    else:
        st.session_state.collect_responses = {}
        st.session_state.collect_step = 0

if "collect_step" not in st.session_state:
    st.session_state.collect_step = 0

current_step = st.session_state.collect_step
total_steps = len(SECTIONS)
section = SECTIONS[current_step]

# Progress bar
st.progress(current_step / total_steps, text=f"Step {current_step + 1} of {total_steps}: {section['title']}")

# Step indicators
step_indicator(SECTIONS, current_step)

st.divider()

# Render current section
section_header(f"Step {current_step + 1}: {section['title']}")

responses = st.session_state.collect_responses

if section["key"] == "header":
    section_data = _render_header_form(responses.get("header", {}))
else:
    items_by_section = _load_codebook_items_by_section()
    section_items = items_by_section.get(section["key"], [])

    if not section_items:
        st.info(f"No items defined for {section['title']}.")
        section_data = {}
    else:
        st.caption(f"{len(section_items)} items in this section")
        section_data = _render_form_section(
            section_items,
            responses.get(section["key"], {}),
        )

# Navigation buttons
st.divider()
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if current_step > 0:
        if st.button("← Previous", use_container_width=True):
            # Save current section
            if section["key"] == "header":
                hdr = dict(section_data)
                if hasattr(hdr.get("assessment_date"), "isoformat"):
                    hdr["assessment_date"] = hdr["assessment_date"].isoformat()
                responses["header"] = hdr
            else:
                responses[section["key"]] = section_data
            st.session_state.collect_responses = responses
            st.session_state.collect_step = current_step - 1
            st.rerun()

with col2:
    if st.button("Save Draft", use_container_width=True):
        if section["key"] == "header":
            # Serialize date for JSON storage
            hdr = dict(section_data)
            if hasattr(hdr.get("assessment_date"), "isoformat"):
                hdr["assessment_date"] = hdr["assessment_date"].isoformat()
            responses["header"] = hdr
        else:
            responses[section["key"]] = section_data
        st.session_state.collect_responses = responses
        save_form_draft(username, current_step, responses)
        st.success("Draft saved!")

with col3:
    if st.button("Clear Form", use_container_width=True):
        st.session_state.collect_responses = {}
        st.session_state.collect_step = 0
        delete_form_draft(username)
        st.rerun()

with col4:
    if current_step < total_steps - 1:
        if st.button("Next →", type="primary", use_container_width=True):
            # Validate header
            if section["key"] == "header":
                if not section_data.get("country"):
                    st.error("Country is required.")
                    st.stop()
                if not section_data.get("district"):
                    st.error("District is required.")
                    st.stop()
                hdr = dict(section_data)
                if hasattr(hdr.get("assessment_date"), "isoformat"):
                    hdr["assessment_date"] = hdr["assessment_date"].isoformat()
                responses["header"] = hdr
            else:
                responses[section["key"]] = section_data
            st.session_state.collect_responses = responses
            st.session_state.collect_step = current_step + 1
            st.rerun()
    else:
        # Final step - submit
        if st.button("Submit & Analyze", type="primary", use_container_width=True):
            responses[section["key"]] = section_data
            st.session_state.collect_responses = responses

            header_data = responses.get("header", {})
            if not header_data.get("country"):
                st.error("Country is required. Go back to Step 1.")
                st.stop()

            # Convert assessment_date to string for serialization
            assess_date = header_data.get("assessment_date")
            header_for_db = {
                "country": header_data["country"],
                "district": header_data.get("district", ""),
                "province": header_data.get("province", ""),
                "assessment_date": assess_date.isoformat() if hasattr(assess_date, 'isoformat') else assess_date,
            }

            # Merge all section responses (flatten for _form_to_parsed_data)
            all_responses = {}
            for sec_key in ["context", "policy", "service_delivery",
                            "human_resources", "supply_chain", "barriers"]:
                all_responses.update(responses.get(sec_key, {}))

            parsed_data = _form_to_parsed_data(all_responses, header_for_db)

            try:
                sehra_id, totals = _run_analysis(parsed_data, header_for_db)

                # Clean up draft
                delete_form_draft(username)
                st.session_state.collect_responses = {}
                st.session_state.collect_step = 0

                st.balloons()
                st.success(f"SEHRA analysis saved! ID: `{sehra_id}`")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Enablers", totals["enabler_count"])
                with col2:
                    st.metric("Total Barriers", totals["barrier_count"])

                st.info("Go to **Dashboard** to view charts and tables, "
                        "or **Export & Share** to download reports.")
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                st.exception(e)
