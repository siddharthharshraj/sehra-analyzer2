"""SSE analysis pipeline for upload and form submission."""

import io
import json
import logging
import tempfile
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sse_starlette.sse import EventSourceResponse

from api.deps import get_current_user
from api.core import db
from api.core.pdf_parser import parse_and_enrich_auto, extract_numeric_data
from api.core.codebook import score_all_items, load_codebook
from api.core.ai_engine import analyze_full_sehra, generate_executive_summary, generate_recommendations, generate_component_summary

logger = logging.getLogger("sehra.routers.analysis")
router = APIRouter()


class FakeUploadedFile:
    """Adapter to make bytes look like a Streamlit UploadedFile for validators."""

    def __init__(self, data: bytes, filename: str, content_type: str = "application/pdf"):
        self._data = data
        self.name = filename
        self.type = content_type
        self.size = len(data)

    def getvalue(self):
        return self._data

    def read(self):
        return self._data


def _emit(step: int, total: int, label: str, progress: float = 0.0) -> str:
    return json.dumps({"event": "progress", "step": step, "total_steps": total, "label": label, "progress": progress})


def _emit_complete(sehra_id: str, enablers: int, barriers: int) -> str:
    return json.dumps({"event": "complete", "sehra_id": sehra_id, "enabler_count": enablers, "barrier_count": barriers})


def _emit_error(message: str) -> str:
    return json.dumps({"event": "error", "message": message})


def _run_upload_pipeline(pdf_bytes: bytes, filename: str):
    """Synchronous pipeline that yields SSE event strings."""
    total_steps = 10

    # Step 1: Validate
    yield _emit(1, total_steps, "Validating PDF...", 0.1)
    from api.core.validators import validate_sehra_pdf
    fake_file = FakeUploadedFile(pdf_bytes, filename)
    try:
        validate_sehra_pdf(fake_file)
    except Exception as e:
        yield _emit_error(f"Validation failed: {e}")
        return

    # Step 2: Parse
    yield _emit(2, total_steps, "Parsing document...", 0.2)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        parsed = parse_and_enrich_auto(tmp_path)
    except Exception as e:
        yield _emit_error(f"Parsing failed: {e}")
        return
    finally:
        import os
        os.unlink(tmp_path)

    header = parsed["header"]

    # Step 3: Score
    yield _emit(3, total_steps, "Scoring items...", 0.3)
    all_items = []
    for comp_data in parsed["components"].values():
        all_items.extend(comp_data.get("items", []))
    scores = score_all_items(all_items)

    # Step 4: AI Analysis
    yield _emit(4, total_steps, "Analyzing components with AI...", 0.4)
    analysis_results = analyze_full_sehra(parsed)

    # Step 5-6: Save to DB
    yield _emit(5, total_steps, "Saving to database...", 0.5)
    sehra_id = db.create_sehra(
        country=header.get("country", ""),
        district=header.get("district", ""),
        province=header.get("province", ""),
        assessment_date=header.get("assessment_date"),
        pdf_filename=filename,
        raw_data=parsed,
    )

    total_enablers = 0
    total_barriers = 0

    # Save component analyses
    components_to_save = ["context", "policy", "service_delivery", "human_resources", "supply_chain", "barriers"]
    for i, comp in enumerate(components_to_save):
        yield _emit(6, total_steps, f"Saving {comp}...", 0.5 + (i * 0.05))

        comp_scores = scores["by_component"].get(comp, {})
        e_count = comp_scores.get("enabler_count", 0)
        b_count = comp_scores.get("barrier_count", 0)
        items = comp_scores.get("items", [])
        total_enablers += e_count
        total_barriers += b_count

        ca_id = db.save_component_analysis(sehra_id, comp, e_count, b_count, items)

        # Save qualitative entries
        ai_result = analysis_results.get(comp, {})
        classifications = ai_result.get("classifications", [])
        if classifications:
            entries = [
                {
                    "remark_text": c.get("remark_text", ""),
                    "item_id": c.get("item_id", ""),
                    "theme": c.get("theme", ""),
                    "classification": c.get("classification", ""),
                    "confidence": c.get("confidence", 0.0),
                }
                for c in classifications
            ]
            db.save_qualitative_entries(ca_id, entries)

        # Save report sections from AI analysis
        has_ai_summaries = False
        for summary_type in ["enabler_summary", "barrier_summary"]:
            summaries = ai_result.get(summary_type, [])
            if summaries:
                combined = "\n\n".join(s.get("summary", "") for s in summaries if s.get("summary"))
                if combined:
                    db.save_report_section(ca_id, summary_type, combined)
                    has_ai_summaries = True

        # Save action points
        action_points = []
        for st in ["enabler_summary", "barrier_summary"]:
            for s in ai_result.get(st, []):
                action_points.extend(s.get("action_points", []))
        if action_points:
            db.save_report_section(ca_id, "action_points", "\n".join(f"- {ap}" for ap in action_points))
            has_ai_summaries = True

        # Fallback: Generate summaries from scored items when AI analysis had no text remarks
        if not has_ai_summaries and items:
            try:
                comp_summary = generate_component_summary(comp, items)
                if comp_summary.get("enabler_summary"):
                    db.save_report_section(ca_id, "enabler_summary", comp_summary["enabler_summary"])
                if comp_summary.get("barrier_summary"):
                    db.save_report_section(ca_id, "barrier_summary", comp_summary["barrier_summary"])
                if comp_summary.get("action_points"):
                    db.save_report_section(ca_id, "action_points", comp_summary["action_points"])
            except Exception as e:
                logger.warning("Failed to generate summary from scored items for %s: %s", comp, e)

    # Step 8: Executive summary
    yield _emit(8, total_steps, "Generating executive summary...", 0.8)
    try:
        exec_summary = generate_executive_summary(
            analysis_results, header, scored_components=scores["by_component"]
        )
    except Exception:
        exec_summary = ""

    # Step 9: Recommendations
    yield _emit(9, total_steps, "Generating recommendations...", 0.9)
    try:
        recommendations = generate_recommendations(
            analysis_results, header, scored_components=scores["by_component"]
        )
    except Exception:
        recommendations = ""

    if exec_summary or recommendations:
        db.save_executive_summary(sehra_id, exec_summary, recommendations)

    # Step 10: Complete
    yield _emit(10, total_steps, "Complete!", 1.0)
    yield _emit_complete(sehra_id, total_enablers, total_barriers)


@router.post("/analyze/upload")
async def analyze_upload(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a PDF and run the full analysis pipeline via SSE."""
    pdf_bytes = await file.read()
    filename = file.filename or "upload.pdf"

    async def event_generator() -> AsyncGenerator[str, None]:
        loop = asyncio.get_event_loop()
        gen = _run_upload_pipeline(pdf_bytes, filename)

        for event_data in gen:
            yield event_data
            await asyncio.sleep(0)  # yield control

    return EventSourceResponse(event_generator())


def _run_form_pipeline(form_data: dict, username: str):
    """Synchronous pipeline for form-submitted data."""
    total_steps = 8

    yield _emit(1, total_steps, "Processing form data...", 0.1)

    header = form_data.get("header", {})
    responses = form_data.get("responses", {})

    # Build items from form responses
    all_items = []
    codebook = load_codebook()
    for item in codebook.get("items", []):
        item_id = item["id"]
        if item_id in responses:
            resp = responses[item_id]
            answer = resp.get("answer") if isinstance(resp, dict) else resp
            remark = resp.get("remark", "") if isinstance(resp, dict) else ""
            all_items.append({
                "item_id": item_id,
                "question": item["question"],
                "answer": answer,
                "remark": remark,
                "component": item["section"],
            })

    # Score
    yield _emit(2, total_steps, "Scoring items...", 0.2)
    scores = score_all_items(all_items)

    # Build parsed-like structure for AI analysis
    parsed = {"header": header, "components": {}}
    for item in all_items:
        comp = item.get("component", "unknown")
        if comp not in parsed["components"]:
            parsed["components"][comp] = {"items": [], "text": ""}
        parsed["components"][comp]["items"].append(item)

    # AI analysis
    yield _emit(3, total_steps, "Analyzing with AI...", 0.3)
    analysis_results = analyze_full_sehra(parsed)

    # Save
    yield _emit(4, total_steps, "Saving to database...", 0.5)
    sehra_id = db.create_sehra(
        country=header.get("country", ""),
        district=header.get("district", ""),
        province=header.get("province", ""),
        assessment_date=header.get("assessment_date"),
        pdf_filename=f"form_{username}",
        raw_data={"source": "form", "responses": responses},
    )

    total_enablers = 0
    total_barriers = 0

    for comp in ["context", "policy", "service_delivery", "human_resources", "supply_chain", "barriers"]:
        comp_scores = scores["by_component"].get(comp, {})
        e_count = comp_scores.get("enabler_count", 0)
        b_count = comp_scores.get("barrier_count", 0)
        items = comp_scores.get("items", [])
        total_enablers += e_count
        total_barriers += b_count

        ca_id = db.save_component_analysis(sehra_id, comp, e_count, b_count, items)

        ai_result = analysis_results.get(comp, {})
        classifications = ai_result.get("classifications", [])
        if classifications:
            entries = [{
                "remark_text": c.get("remark_text", ""),
                "item_id": c.get("item_id", ""),
                "theme": c.get("theme", ""),
                "classification": c.get("classification", ""),
                "confidence": c.get("confidence", 0.0),
            } for c in classifications]
            db.save_qualitative_entries(ca_id, entries)

        has_ai_summaries = False
        for summary_type in ["enabler_summary", "barrier_summary"]:
            summaries = ai_result.get(summary_type, [])
            if summaries:
                combined = "\n\n".join(s.get("summary", "") for s in summaries if s.get("summary"))
                if combined:
                    db.save_report_section(ca_id, summary_type, combined)
                    has_ai_summaries = True

        # Fallback: Generate summaries from scored items
        if not has_ai_summaries and items:
            try:
                comp_summary = generate_component_summary(comp, items)
                if comp_summary.get("enabler_summary"):
                    db.save_report_section(ca_id, "enabler_summary", comp_summary["enabler_summary"])
                if comp_summary.get("barrier_summary"):
                    db.save_report_section(ca_id, "barrier_summary", comp_summary["barrier_summary"])
                if comp_summary.get("action_points"):
                    db.save_report_section(ca_id, "action_points", comp_summary["action_points"])
            except Exception:
                pass

    yield _emit(6, total_steps, "Generating executive summary...", 0.8)
    try:
        exec_summary = generate_executive_summary(
            analysis_results, header, scored_components=scores["by_component"]
        )
        recommendations = generate_recommendations(
            analysis_results, header, scored_components=scores["by_component"]
        )
        db.save_executive_summary(sehra_id, exec_summary, recommendations)
    except Exception:
        pass

    # Delete draft after successful submission
    db.delete_form_draft(username)

    yield _emit(8, total_steps, "Complete!", 1.0)
    yield _emit_complete(sehra_id, total_enablers, total_barriers)


@router.post("/analyze/form")
async def analyze_form(
    form_data: dict,
    user: dict = Depends(get_current_user),
):
    """Submit form data and run the full analysis pipeline via SSE."""
    username = user["sub"]

    async def event_generator() -> AsyncGenerator[str, None]:
        gen = _run_form_pipeline(form_data, username)
        for event_data in gen:
            yield event_data
            await asyncio.sleep(0)

    return EventSourceResponse(event_generator())
