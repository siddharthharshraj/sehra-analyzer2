"""HTML report generator using Jinja2 + Plotly.

Generates a self-contained HTML report string that can be:
- Rendered inline via st.components.v1.html()
- Cached in SharedReport.cached_html for share links
- Downloaded as an HTML file
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from core.charts import (
    create_radar_chart, create_theme_heatmap,
    create_enabler_barrier_bar, create_component_bar,
    build_theme_data_from_analyses,
    COMPONENT_ORDER,
)

logger = logging.getLogger("sehra.report_html")

COMPONENT_DISPLAY_NAMES = {
    "context": "Context",
    "policy": "Sectoral Legislation, Policy and Strategy",
    "service_delivery": "Institutional and Service Delivery Environment",
    "human_resources": "Human Resources",
    "supply_chain": "Supply Chain",
    "barriers": "Barriers",
}

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def generate_html_report(
    component_analyses: list[dict],
    header_info: dict,
    executive_summary: str = "",
    recommendations: str = "",
) -> str:
    """Generate a self-contained HTML report.

    Args:
        component_analyses: List of component analysis dicts from DB
        header_info: {country, district, assessment_date}
        executive_summary: Optional executive summary text
        recommendations: Optional recommendations text

    Returns:
        Self-contained HTML string
    """
    logger.info("Generating HTML report for %s", header_info.get("country", ""))

    comp_lookup = {ca["component"]: ca for ca in component_analyses}

    # Calculate totals
    total_enablers = sum(a.get("enabler_count", 0) for a in component_analyses)
    total_barriers = sum(a.get("barrier_count", 0) for a in component_analyses)
    total_remarks = sum(len(a.get("qualitative_entries", [])) for a in component_analyses)
    grand_total = total_enablers + total_barriers
    readiness_score = round(total_enablers / grand_total * 100) if grand_total > 0 else 0

    # Build component scores for radar chart
    comp_scores = {}
    for ca in component_analyses:
        comp_scores[ca["component"]] = {
            "enabler_count": ca.get("enabler_count", 0),
            "barrier_count": ca.get("barrier_count", 0),
        }

    # Generate charts
    radar_fig, _ = create_radar_chart(comp_scores)
    radar_html = radar_fig.to_html(full_html=False, include_plotlyjs=False)

    bar_data = []
    for comp in COMPONENT_ORDER:
        ca = comp_lookup.get(comp)
        if ca:
            bar_data.append({
                "name": COMPONENT_DISPLAY_NAMES.get(comp, comp),
                "enabler_count": ca.get("enabler_count", 0),
                "barrier_count": ca.get("barrier_count", 0),
            })

    overall_fig, _ = create_enabler_barrier_bar(bar_data)
    overall_bar_html = overall_fig.to_html(full_html=False, include_plotlyjs=False)

    theme_data = build_theme_data_from_analyses(component_analyses)
    heatmap_html = ""
    if theme_data:
        heatmap_fig, _ = create_theme_heatmap(theme_data)
        heatmap_html = heatmap_fig.to_html(full_html=False, include_plotlyjs=False)

    # Build per-component data
    components = []
    appendix_entries = []

    for comp_key in COMPONENT_ORDER:
        ca = comp_lookup.get(comp_key)
        if not ca:
            continue

        entries = ca.get("qualitative_entries", [])
        enabler_entries = [e for e in entries if e.get("classification") in ("enabler", "strength")]
        barrier_entries = [e for e in entries if e.get("classification") in ("barrier", "weakness")]

        # Component chart
        comp_fig, _ = create_component_bar(
            ca.get("enabler_count", 0),
            ca.get("barrier_count", 0),
            COMPONENT_DISPLAY_NAMES.get(comp_key, comp_key),
        )
        comp_chart_html = comp_fig.to_html(full_html=False, include_plotlyjs=False)

        # Report sections
        sections = ca.get("report_sections", {})
        enabler_summary_text = sections.get("enabler_summary", {}).get("content", "")
        barrier_summary_text = sections.get("barrier_summary", {}).get("content", "")
        action_points_text = sections.get("action_points", {}).get("content", "")

        components.append({
            "key": comp_key,
            "display_name": COMPONENT_DISPLAY_NAMES.get(comp_key, comp_key),
            "enabler_count": ca.get("enabler_count", 0),
            "barrier_count": ca.get("barrier_count", 0),
            "chart_html": comp_chart_html,
            "enabler_entries": enabler_entries,
            "barrier_entries": barrier_entries,
            "enabler_summary": enabler_summary_text,
            "barrier_summary": barrier_summary_text,
            "action_points": action_points_text,
        })

        # Appendix entries
        for e in entries:
            appendix_entries.append({
                "component": COMPONENT_DISPLAY_NAMES.get(comp_key, comp_key),
                "theme": e.get("theme", ""),
                "classification": e.get("classification", ""),
                "confidence": e.get("confidence", 0),
                "remark_text": e.get("remark_text", ""),
            })

    # Render template
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("report.html")

    html = template.render(
        header=header_info,
        executive_summary=executive_summary,
        total_enablers=total_enablers,
        total_barriers=total_barriers,
        total_remarks=total_remarks,
        readiness_score=readiness_score,
        radar_chart_html=radar_html,
        overall_bar_html=overall_bar_html,
        heatmap_html=heatmap_html,
        components=components,
        recommendations=recommendations,
        appendix_entries=appendix_entries,
    )

    logger.info("HTML report generated: %d bytes", len(html))
    return html
