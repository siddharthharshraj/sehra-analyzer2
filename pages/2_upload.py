"""Page 2: Upload SEHRA PDF and trigger analysis pipeline."""

import logging
import streamlit as st
import tempfile
import os
import json
import time

from core.pdf_parser import parse_and_enrich, parse_and_enrich_auto
from core.codebook import score_all_items, COMPONENT_NAMES
from core.ai_engine import analyze_full_sehra, generate_executive_summary, generate_recommendations
from core.validators import validate_sehra_pdf
from core.exceptions import ValidationError
from core.db import (
    create_sehra, save_component_analysis,
    save_qualitative_entries, save_report_section,
    save_executive_summary,
)
from core.ui_theme import page_header

logger = logging.getLogger("sehra.upload")

page_header("Upload SEHRA PDF", "Upload a completed SEHRA Scoping Module PDF for automated analysis.")

uploaded_file = st.file_uploader(
    "Choose a SEHRA PDF file",
    type=["pdf"],
    help="Upload a completed SEHRA Scoping Module PDF (max 10MB)",
)

if uploaded_file is not None:
    st.success(f"File uploaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.0f} KB)")

    # Validate PDF before proceeding
    validation_ok = False
    try:
        val_info = validate_sehra_pdf(uploaded_file)
        if val_info.get("is_scanned"):
            st.warning(
                f"Scanned PDF detected ({val_info['pages']} pages, no form fields) "
                "— will use OCR (this takes longer)"
            )
        else:
            st.info(f"PDF validated: {val_info['pages']} pages, {val_info['widgets_on_page1']} form fields on page 1")
        validation_ok = True
    except ValidationError as e:
        st.error(f"PDF validation failed: {e}")
        logger.warning("PDF validation failed for %s: %s", uploaded_file.name, e)

    if validation_ok and st.button("Start Analysis", type="primary", use_container_width=True):
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            progress = st.progress(0, text="Starting analysis...")
            status = st.status("Analysis Pipeline", expanded=True)

            # Step 1: Parse PDF
            with status:
                st.write("**Step 1/5:** Parsing PDF...")
            progress.progress(10, text="Parsing PDF...")

            if val_info.get("is_scanned"):
                parsed = parse_and_enrich_auto(tmp_path)
            else:
                parsed = parse_and_enrich(tmp_path)
            header = parsed["header"]

            with status:
                st.write(f"  Country: **{header.get('country', 'Unknown')}**")
                st.write(f"  District: **{header.get('district', 'Unknown')}**")
                total_items = sum(len(c.get("items", [])) for c in parsed["components"].values())
                st.write(f"  Items extracted: **{total_items}**")

            progress.progress(30, text="PDF parsed successfully")

            # Step 2: Quantitative scoring
            with status:
                st.write("**Step 2/5:** Scoring items (quantitative analysis)...")
            progress.progress(40, text="Scoring items...")

            # Flatten all items for scoring
            all_items = []
            for comp_name, comp_data in parsed["components"].items():
                for item in comp_data.get("items", []):
                    all_items.append({**item, "component": comp_name})

            scores = score_all_items(all_items)

            with status:
                totals = scores["totals"]
                st.write(f"  Total enablers: **{totals['enabler_count']}**")
                st.write(f"  Total barriers: **{totals['barrier_count']}**")

            progress.progress(50, text="Scoring complete")

            # Step 3: AI Qualitative Analysis
            with status:
                st.write("**Step 3/5:** AI qualitative analysis (this may take 1-2 minutes)...")
            progress.progress(55, text="Running AI analysis...")

            ai_results = analyze_full_sehra(parsed)

            with status:
                total_classified = sum(
                    len(r.get("classifications", []))
                    for r in ai_results.values()
                )
                st.write(f"  Remarks classified: **{total_classified}**")

            progress.progress(80, text="AI analysis complete")

            # Step 4: Save to database
            with status:
                st.write("**Step 4/5:** Saving results...")
            progress.progress(80, text="Saving to database...")

            # Create SEHRA record
            sehra_id = create_sehra(
                country=header.get("country", "Unknown"),
                district=header.get("district", ""),
                province=header.get("province", ""),
                assessment_date=None,  # Parse from header if available
                pdf_filename=uploaded_file.name,
                raw_data={"header": header, "components_summary": {
                    k: {"item_count": len(v.get("items", []))}
                    for k, v in parsed["components"].items()
                }},
            )

            # Save component analyses
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

                # Save qualitative entries
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

                # Save report sections (summaries)
                for summary_type in ["enabler_summary", "barrier_summary"]:
                    summaries = comp_ai.get(summary_type, [])
                    if summaries:
                        content = "\n\n".join(
                            f"**{', '.join(s.get('themes', []))}**: {s.get('summary', '')}"
                            + ("\n\nAction Points:\n" + "\n".join(f"- {ap}" for ap in s.get('action_points', [])))
                            for s in summaries
                        )
                        save_report_section(ca_id, summary_type, content)

                # Save action points
                all_action_points = []
                for summary_type in ["enabler_summary", "barrier_summary"]:
                    for s in comp_ai.get(summary_type, []):
                        all_action_points.extend(s.get("action_points", []))
                if all_action_points:
                    save_report_section(
                        ca_id, "action_points",
                        "\n".join(f"- {ap}" for ap in all_action_points)
                    )

            progress.progress(88, text="Database saved")

            # Step 5: Generate executive summary & recommendations
            with status:
                st.write("**Step 5/5:** Generating executive summary & recommendations...")
            progress.progress(90, text="Generating executive summary...")

            try:
                exec_summary = generate_executive_summary(ai_results, header)
                recommendations = generate_recommendations(ai_results, header)
                save_executive_summary(sehra_id, exec_summary, recommendations)
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

            # Show summary
            st.balloons()
            st.success(f"SEHRA analysis saved! ID: `{sehra_id}`")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Enablers", totals["enabler_count"])
            with col2:
                st.metric("Total Barriers", totals["barrier_count"])

            st.info("Go to **Review Analysis** to review and edit the results, "
                    "or **Dashboard** to view charts and tables.")

        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
            st.exception(e)

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

else:
    st.info("Please upload a SEHRA Scoping Module PDF to begin analysis.")

    with st.expander("What is SEHRA?"):
        st.markdown("""
        **School Eye Health Rapid Assessment (SEHRA)** is a structured PDF-based survey tool
        by [Peek Vision](https://peekvision.org) used globally to assess readiness for school
        eye health programmes.

        Each SEHRA has:
        - **309 items** across **7 sections** (Context, 5 Components, Summary)
        - **5 Components**: Policy & Strategy, Service Delivery, Human Resources, Supply Chain, Barriers
        - Each item has: **Yes/No answer** + **free-text Remarks**

        This tool automates the analysis process, reducing analysis time from ~2 months to hours.
        """)
