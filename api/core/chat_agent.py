"""AI Chat Agent for interactive SEHRA data queries.

Processes natural language questions about SEHRA data, returning
text answers and optional Plotly charts.
"""

import json
import logging
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pydantic import BaseModel

from core.ai_engine import _call_llm, _parse_llm_json
from core.charts import (
    TEAL, RED, COMPONENT_ORDER,
    COMPONENT_SHORT_NAMES,
)

logger = logging.getLogger("sehra.chat_agent")


class ChatResponse(BaseModel):
    text: str
    chart: Optional[dict] = None  # Plotly figure JSON
    data_table: Optional[list] = None  # Rows for DataFrame display


def _build_data_context(component_analyses: list[dict], exec_summary: str = "",
                        country: str = "") -> str:
    """Build a data context string for the LLM.

    Args:
        component_analyses: List of component analysis dicts from DB
        exec_summary: Optional executive summary text
        country: Country name for context
    """
    lines = ["SEHRA DATA SUMMARY:"]
    if country:
        lines.append(f"Country: {country}")

    total_enablers = 0
    total_barriers = 0
    total_remarks = 0

    for ca in component_analyses:
        comp = ca.get("component", "")
        name = COMPONENT_SHORT_NAMES.get(comp, comp)
        e = ca.get("enabler_count", 0)
        b = ca.get("barrier_count", 0)
        entries = ca.get("qualitative_entries", [])
        remarks = len(entries)
        total_enablers += e
        total_barriers += b
        total_remarks += remarks

        lines.append(f"\n{name}: {e} enablers, {b} barriers, {remarks} classified remarks")

        # Theme breakdown
        themes = {}
        for entry in entries:
            theme = entry.get("theme", "Other")
            cls = entry.get("classification", "")
            if theme not in themes:
                themes[theme] = {"enabler": 0, "barrier": 0, "strength": 0, "weakness": 0}
            if cls in themes[theme]:
                themes[theme][cls] += 1

        if themes:
            for theme, counts in themes.items():
                e_count = counts["enabler"] + counts["strength"]
                b_count = counts["barrier"] + counts["weakness"]
                if e_count or b_count:
                    lines.append(f"  Theme '{theme}': {e_count} enablers, {b_count} barriers")

        # Report sections
        sections = ca.get("report_sections", {})
        for sec_type, sec_data in sections.items():
            content = sec_data.get("content", "")
            if content:
                lines.append(f"  {sec_type}: {content[:200]}...")

    grand_total = total_enablers + total_barriers
    readiness = round(total_enablers / grand_total * 100) if grand_total > 0 else 0
    lines.insert(1, f"Overall: {total_enablers} enablers, {total_barriers} barriers, "
                    f"{readiness}% readiness, {total_remarks} classified remarks")

    if exec_summary:
        lines.append(f"\nEXECUTIVE SUMMARY:\n{exec_summary[:500]}")

    return "\n".join(lines)


def _build_chart_system_prompt() -> str:
    return """You are an AI assistant for SEHRA (School Eye Health Rapid Assessment) data analysis.
You have access to the assessment data and can answer questions about enablers, barriers,
themes, components, readiness scores, and recommendations.

When the user asks for a chart or visualization, include a `chart_spec` in your response
with the chart type and data. Available chart types:
- "bar": Grouped or simple bar chart
- "pie": Pie chart
- "radar": Radar/spider chart (already available in dashboard)

For text-only answers, just provide clear, concise text.

Respond with JSON:
{
  "answer": "Your text answer here",
  "chart_spec": {
    "type": "bar",
    "title": "Chart Title",
    "data": [{"label": "X", "value": 10, "group": "Enablers"}],
    "x_label": "Component",
    "y_label": "Count"
  }
}

If no chart is needed, set chart_spec to null.
Always respond with valid JSON only."""


def _create_chart_from_spec(spec: dict) -> go.Figure | None:
    """Create a Plotly figure from a chart specification."""
    if not spec:
        return None

    chart_type = spec.get("type", "bar")
    title = spec.get("title", "")
    data = spec.get("data", [])

    if not data:
        return None

    try:
        if chart_type == "bar":
            df = pd.DataFrame(data)
            if "group" in df.columns:
                fig = px.bar(df, x="label", y="value", color="group",
                             barmode="group", title=title,
                             color_discrete_map={"Enablers": TEAL, "Barriers": RED,
                                                 "enabler": TEAL, "barrier": RED,
                                                 "Strengths": TEAL, "Weaknesses": RED})
            else:
                colors = [TEAL if i % 2 == 0 else RED for i in range(len(df))]
                fig = px.bar(df, x="label", y="value", title=title,
                             color_discrete_sequence=[TEAL])
            fig.update_layout(
                xaxis_title=spec.get("x_label", ""),
                yaxis_title=spec.get("y_label", ""),
                height=400,
            )
            return fig

        elif chart_type == "pie":
            df = pd.DataFrame(data)
            fig = px.pie(df, names="label", values="value", title=title)
            fig.update_layout(height=400)
            return fig

        elif chart_type == "radar":
            labels = [d["label"] for d in data]
            values = [d["value"] for d in data]
            labels_closed = labels + [labels[0]]
            values_closed = values + [values[0]]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values_closed, theta=labels_closed,
                fill='toself', fillcolor=f"rgba(13, 115, 119, 0.3)",
                line=dict(color=TEAL, width=2),
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                title=title, height=400, showlegend=False,
            )
            return fig

    except Exception as e:
        logger.warning("Failed to create chart from spec: %s", e)
        return None


def chat_query(question: str, component_analyses: list[dict],
               executive_summary: str = "", country: str = "") -> ChatResponse:
    """Process a user question about SEHRA data.

    Args:
        question: User's natural language question
        component_analyses: List of component analysis dicts from DB
        executive_summary: Optional executive summary text
        country: Country name for context in AI responses

    Returns:
        ChatResponse with text answer and optional chart
    """
    data_context = _build_data_context(component_analyses, executive_summary, country=country)
    system_prompt = _build_chart_system_prompt()

    user_message = f"""DATA:
{data_context}

USER QUESTION: {question}

Respond with JSON only."""

    try:
        response_text = _call_llm(system_prompt, user_message)
        result = _parse_llm_json(response_text)

        answer = result.get("answer", response_text)
        chart_spec = result.get("chart_spec")

        chart_json = None
        if chart_spec:
            fig = _create_chart_from_spec(chart_spec)
            if fig:
                chart_json = json.loads(fig.to_json())

        return ChatResponse(
            text=answer,
            chart=chart_json,
        )

    except Exception as e:
        logger.error("Chat query failed: %s", e)
        return ChatResponse(
            text=f"I'm sorry, I couldn't process that question. Error: {str(e)[:200]}",
        )
