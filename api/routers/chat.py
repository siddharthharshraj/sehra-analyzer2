"""Chat endpoint for AI-powered SEHRA data queries."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user
from api.schemas import ChatRequest, ChatResponse
from api.core import db
from api.core.chat_agent import chat_query

logger = logging.getLogger("sehra.routers.chat")
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    """Process a natural language question about SEHRA data."""
    sehra = db.get_sehra(req.sehra_id)
    if not sehra:
        raise HTTPException(status_code=404, detail="SEHRA not found")

    component_analyses = db.get_component_analyses(req.sehra_id)
    exec_summary = sehra.get("executive_summary", "")

    result = chat_query(req.question, component_analyses, exec_summary)

    # Convert Plotly chart JSON to simple chart_spec for Recharts
    chart_spec = None
    if result.chart:
        chart_spec = _plotly_to_recharts(result.chart)

    return ChatResponse(text=result.text, chart_spec=chart_spec)


def _plotly_to_recharts(plotly_json: dict) -> dict | None:
    """Convert Plotly figure JSON to a simple chart spec for Recharts."""
    try:
        data_list = plotly_json.get("data", [])
        layout = plotly_json.get("layout", {})
        title = layout.get("title", {})
        if isinstance(title, dict):
            title = title.get("text", "")

        if not data_list:
            return None

        first_trace = data_list[0]
        trace_type = first_trace.get("type", "bar")

        if trace_type in ("bar", "histogram"):
            chart_data = []
            for trace in data_list:
                group = trace.get("name", "")
                x_vals = trace.get("x", [])
                y_vals = trace.get("y", [])
                for x, y in zip(x_vals, y_vals):
                    chart_data.append({"label": str(x), "value": y, "group": group})
            return {"type": "bar", "title": title, "data": chart_data}

        elif trace_type == "pie":
            labels = first_trace.get("labels", [])
            values = first_trace.get("values", [])
            chart_data = [{"label": l, "value": v} for l, v in zip(labels, values)]
            return {"type": "pie", "title": title, "data": chart_data}

        elif trace_type == "scatterpolar":
            theta = first_trace.get("theta", [])
            r = first_trace.get("r", [])
            chart_data = [{"label": t, "value": v} for t, v in zip(theta, r)]
            return {"type": "radar", "title": title, "data": chart_data}

        return None
    except Exception as e:
        logger.warning("Failed to convert Plotly to Recharts: %s", e)
        return None
