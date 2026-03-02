"""Agent tool definitions and implementations for the SEHRA Copilot.

Each tool wraps existing db/codebook functions and returns JSON-serializable dicts.
Tool schemas are in OpenAI function-calling format.
"""

import logging
from api.core import db
from api.core import codebook_admin

logger = logging.getLogger("sehra.agent_tools")

# ---------------------------------------------------------------------------
# OpenAI function-calling tool schemas
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_assessments",
            "description": "List all SEHRA assessments with their ID, country, district, status, and date.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_assessment_details",
            "description": "Get detailed info for a single SEHRA assessment including executive summary and recommendations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sehra_id": {"type": "string", "description": "The SEHRA assessment ID"},
                },
                "required": ["sehra_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_component_analysis",
            "description": "Get component-level analysis for a SEHRA: enabler/barrier counts, qualitative entries, and report sections per component.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sehra_id": {"type": "string", "description": "The SEHRA assessment ID"},
                },
                "required": ["sehra_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_executive_summary",
            "description": "Get the executive summary and recommendations text for a SEHRA assessment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sehra_id": {"type": "string", "description": "The SEHRA assessment ID"},
                },
                "required": ["sehra_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_entries",
            "description": "Search and filter qualitative entries across all components of a SEHRA. Filter by theme, classification (enabler/barrier), minimum confidence, or text substring.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sehra_id": {"type": "string", "description": "The SEHRA assessment ID"},
                    "theme": {"type": "string", "description": "Filter by theme (e.g. Infrastructure, Funding, Training)"},
                    "classification": {"type": "string", "description": "Filter by classification: enabler, barrier, strength, weakness"},
                    "min_confidence": {"type": "number", "description": "Minimum confidence threshold (0.0-1.0)"},
                    "text_query": {"type": "string", "description": "Substring to search for in remark text (case-insensitive)"},
                },
                "required": ["sehra_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_assessments",
            "description": "Compare two SEHRA assessments side by side, showing enabler/barrier counts per component.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sehra_id_a": {"type": "string", "description": "First SEHRA assessment ID"},
                    "sehra_id_b": {"type": "string", "description": "Second SEHRA assessment ID"},
                },
                "required": ["sehra_id_a", "sehra_id_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_codebook",
            "description": "Get the codebook structure: list of sections and their items/questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "section": {"type": "string", "description": "Optional section name to filter (e.g. context, policy). If omitted, returns all sections."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_actions",
            "description": "Inspect the current state of a SEHRA assessment and return suggested actions the user can take (e.g. batch approve entries, change status, export).",
            "parameters": {
                "type": "object",
                "properties": {
                    "sehra_id": {"type": "string", "description": "The SEHRA assessment ID"},
                },
                "required": ["sehra_id"],
            },
        },
    },
    # --- Write tools (agent can directly edit analysis data) ---
    {
        "type": "function",
        "function": {
            "name": "edit_entry",
            "description": "Edit a qualitative entry's theme and/or classification. Use this when the user asks to change, fix, or reclassify an entry.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entry_id": {"type": "string", "description": "The qualitative entry ID to edit"},
                    "theme": {"type": "string", "description": "New theme (e.g. Infrastructure, Funding, Training). Omit to keep current."},
                    "classification": {"type": "string", "description": "New classification: enabler, barrier, strength, or weakness. Omit to keep current."},
                },
                "required": ["entry_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_report_section",
            "description": "Edit a report section's content. Use this when the user asks to rewrite, fix, or update a report section.",
            "parameters": {
                "type": "object",
                "properties": {
                    "section_id": {"type": "string", "description": "The report section ID to edit"},
                    "content": {"type": "string", "description": "The new content for the section"},
                },
                "required": ["section_id", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_executive_summary",
            "description": "Edit the executive summary and/or recommendations for a SEHRA assessment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sehra_id": {"type": "string", "description": "The SEHRA assessment ID"},
                    "executive_summary": {"type": "string", "description": "New executive summary text. Omit to keep current."},
                    "recommendations": {"type": "string", "description": "New recommendations text. Omit to keep current."},
                },
                "required": ["sehra_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "change_status",
            "description": "Change the status of a SEHRA assessment. Valid statuses: draft, reviewed, published.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sehra_id": {"type": "string", "description": "The SEHRA assessment ID"},
                    "status": {"type": "string", "enum": ["draft", "reviewed", "published"], "description": "New status"},
                },
                "required": ["sehra_id", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "batch_approve",
            "description": "Approve all qualitative entries above a confidence threshold, marking them as human-reviewed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sehra_id": {"type": "string", "description": "The SEHRA assessment ID"},
                    "confidence_threshold": {"type": "number", "description": "Minimum confidence (0.0-1.0). Default 0.8."},
                },
                "required": ["sehra_id"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def list_assessments() -> dict:
    """List all SEHRA assessments."""
    sehras = db.list_sehras()
    return {"assessments": sehras, "count": len(sehras)}


def get_assessment_details(sehra_id: str) -> dict:
    """Get SEHRA detail + executive summary."""
    sehra = db.get_sehra(sehra_id)
    if not sehra:
        return {"error": f"Assessment {sehra_id} not found"}
    # Remove raw_extracted_data to keep response compact
    sehra.pop("raw_extracted_data", None)
    return sehra


def get_component_analysis(sehra_id: str) -> dict:
    """Get component analyses with entries and sections."""
    components = db.get_component_analyses(sehra_id)
    if not components:
        return {"error": f"No components found for assessment {sehra_id}", "components": []}
    # Summarize to keep token usage manageable
    summary = []
    for comp in components:
        entry_count = len(comp.get("qualitative_entries", []))
        summary.append({
            "component": comp["component"],
            "enabler_count": comp["enabler_count"],
            "barrier_count": comp["barrier_count"],
            "entry_count": entry_count,
            "report_sections": {
                k: v["content"][:500] for k, v in comp.get("report_sections", {}).items()
            },
            "qualitative_entries": comp.get("qualitative_entries", [])[:20],
        })
    return {"sehra_id": sehra_id, "components": summary}


def get_executive_summary(sehra_id: str) -> dict:
    """Get executive summary and recommendations."""
    return db.get_executive_summary(sehra_id)


def search_entries(sehra_id: str, theme: str = None, classification: str = None,
                   min_confidence: float = None, text_query: str = None) -> dict:
    """Search and filter qualitative entries."""
    components = db.get_component_analyses(sehra_id)
    results = []
    for comp in components:
        for entry in comp.get("qualitative_entries", []):
            if theme and entry["theme"].lower() != theme.lower():
                continue
            if classification and entry["classification"].lower() != classification.lower():
                continue
            if min_confidence is not None and entry["confidence"] < min_confidence:
                continue
            if text_query and text_query.lower() not in entry["remark_text"].lower():
                continue
            results.append({
                **entry,
                "component": comp["component"],
            })
    return {"entries": results, "count": len(results)}


def compare_assessments(sehra_id_a: str, sehra_id_b: str) -> dict:
    """Compare two SEHRAs side by side."""
    sehra_a = db.get_sehra(sehra_id_a)
    sehra_b = db.get_sehra(sehra_id_b)
    if not sehra_a:
        return {"error": f"Assessment {sehra_id_a} not found"}
    if not sehra_b:
        return {"error": f"Assessment {sehra_id_b} not found"}

    comps_a = db.get_component_analyses(sehra_id_a)
    comps_b = db.get_component_analyses(sehra_id_b)

    def summarize(comps):
        return {
            c["component"]: {
                "enabler_count": c["enabler_count"],
                "barrier_count": c["barrier_count"],
                "entry_count": len(c.get("qualitative_entries", [])),
            }
            for c in comps
        }

    return {
        "assessment_a": {
            "id": sehra_a["id"],
            "country": sehra_a["country"],
            "district": sehra_a["district"],
            "status": sehra_a["status"],
            "components": summarize(comps_a),
        },
        "assessment_b": {
            "id": sehra_b["id"],
            "country": sehra_b["country"],
            "district": sehra_b["district"],
            "status": sehra_b["status"],
            "components": summarize(comps_b),
        },
    }


def get_codebook(section: str = None) -> dict:
    """Get codebook sections and items. Returns compact summaries to stay within token limits."""
    if section:
        items = codebook_admin.get_items_by_section(section)
        # Return compact view: id, question (truncated), scoring info
        compact = [
            {"id": it["id"], "question": it["question"][:100], "has_scoring": it["has_scoring"]}
            for it in items
        ]
        return {"section": section, "items": compact, "count": len(compact)}
    sections = codebook_admin.get_sections()
    result = {}
    for s in sections:
        items = codebook_admin.get_items_by_section(s)
        result[s] = {
            "count": len(items),
            "sample_questions": [it["question"][:80] for it in items[:3]],
        }
    return {"sections": result}


def suggest_actions(sehra_id: str) -> dict:
    """Inspect state and return actionable suggestions."""
    sehra = db.get_sehra(sehra_id)
    if not sehra:
        return {"error": f"Assessment {sehra_id} not found"}

    components = db.get_component_analyses(sehra_id)

    # Count entries by review status
    total_entries = 0
    unreviewed = 0
    high_confidence_unreviewed = 0
    for comp in components:
        for entry in comp.get("qualitative_entries", []):
            total_entries += 1
            if not entry.get("edited_by_human"):
                unreviewed += 1
                if entry.get("confidence", 0) >= 0.8:
                    high_confidence_unreviewed += 1

    actions = []

    # Batch approve suggestion
    if high_confidence_unreviewed > 0:
        actions.append({
            "label": f"Approve {high_confidence_unreviewed} high-confidence entries",
            "description": f"Auto-approve {high_confidence_unreviewed} entries with >=80% confidence",
            "api_call": {
                "method": "POST",
                "path": f"/sehras/{sehra_id}/batch-approve",
                "body": {"confidence_threshold": 0.8},
            },
        })

    # Status transitions
    status = sehra["status"]
    if status == "draft" and unreviewed == 0 and total_entries > 0:
        actions.append({
            "label": "Mark as Reviewed",
            "description": "All entries have been reviewed. Mark this assessment as reviewed.",
            "api_call": {
                "method": "PATCH",
                "path": f"/sehras/{sehra_id}/status",
                "body": {"status": "reviewed"},
            },
        })
    elif status == "reviewed":
        actions.append({
            "label": "Publish Assessment",
            "description": "Publish this assessment to make it available for export and sharing.",
            "api_call": {
                "method": "PATCH",
                "path": f"/sehras/{sehra_id}/status",
                "body": {"status": "published"},
            },
        })

    # Export suggestions
    if total_entries > 0:
        actions.append({
            "label": "Export as DOCX",
            "description": "Download the full report as a Word document.",
            "api_call": {
                "method": "GET",
                "path": f"/export/{sehra_id}/docx",
                "download": True,
            },
        })

    return {
        "sehra_id": sehra_id,
        "status": status,
        "total_entries": total_entries,
        "unreviewed_entries": unreviewed,
        "high_confidence_unreviewed": high_confidence_unreviewed,
        "actions": actions,
    }


# ---------------------------------------------------------------------------
# Write tool implementations
# ---------------------------------------------------------------------------


def edit_entry(entry_id: str, theme: str = None, classification: str = None) -> dict:
    """Edit a qualitative entry's theme and/or classification."""
    if not theme and not classification:
        return {"error": "Provide at least one of 'theme' or 'classification' to edit."}
    db.update_qualitative_entry(entry_id, theme=theme, classification=classification)
    return {
        "success": True,
        "entry_id": entry_id,
        "updated_fields": {
            k: v for k, v in {"theme": theme, "classification": classification}.items() if v
        },
    }


def edit_report_section(section_id: str, content: str) -> dict:
    """Edit a report section's content."""
    db.update_report_section(section_id, content)
    return {"success": True, "section_id": section_id, "content_length": len(content)}


def edit_executive_summary(sehra_id: str, executive_summary: str = None,
                           recommendations: str = None) -> dict:
    """Edit executive summary and/or recommendations."""
    current = db.get_executive_summary(sehra_id)
    if "error" in current:
        return current
    new_summary = executive_summary if executive_summary is not None else current.get("executive_summary", "")
    new_recs = recommendations if recommendations is not None else current.get("recommendations", "")
    db.save_executive_summary(sehra_id, new_summary, new_recs)
    return {
        "success": True,
        "sehra_id": sehra_id,
        "updated": [k for k, v in {"executive_summary": executive_summary, "recommendations": recommendations}.items() if v is not None],
    }


def change_status(sehra_id: str, status: str) -> dict:
    """Change SEHRA assessment status."""
    if status not in ("draft", "reviewed", "published"):
        return {"error": f"Invalid status '{status}'. Must be draft, reviewed, or published."}
    db.update_sehra_status(sehra_id, status)
    return {"success": True, "sehra_id": sehra_id, "new_status": status}


def batch_approve(sehra_id: str, confidence_threshold: float = 0.8) -> dict:
    """Batch approve entries above confidence threshold."""
    count = db.batch_approve_entries(sehra_id, confidence_threshold)
    return {"success": True, "sehra_id": sehra_id, "approved_count": count}


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "list_assessments": list_assessments,
    "get_assessment_details": get_assessment_details,
    "get_component_analysis": get_component_analysis,
    "get_executive_summary": get_executive_summary,
    "search_entries": search_entries,
    "compare_assessments": compare_assessments,
    "get_codebook": get_codebook,
    "suggest_actions": suggest_actions,
    "edit_entry": edit_entry,
    "edit_report_section": edit_report_section,
    "edit_executive_summary": edit_executive_summary,
    "change_status": change_status,
    "batch_approve": batch_approve,
}


def execute_tool(name: str, arguments: dict) -> dict:
    """Execute a tool by name with the given arguments. Returns JSON-serializable dict."""
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return {"error": f"Unknown tool: {name}"}
    try:
        return func(**arguments)
    except Exception as e:
        logger.exception("Tool %s failed", name)
        return {"error": f"Tool {name} failed: {str(e)}"}
