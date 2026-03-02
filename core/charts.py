"""Shared chart generation module returning (plotly_fig, png_bytes) tuples.

Used by both DOCX report generation and HTML report/dashboard.
"""

import io
import logging

import plotly.graph_objects as go
import plotly.express as px
import numpy as np

logger = logging.getLogger("sehra.charts")

TEAL = "#0D7377"
RED = "#CC3333"
LIGHT_TEAL = "rgba(13, 115, 119, 0.3)"
LIGHT_RED = "rgba(204, 51, 51, 0.3)"

CHART_FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

COMPONENT_ORDER = ["context", "policy", "service_delivery",
                    "human_resources", "supply_chain", "barriers"]

COMPONENT_SHORT_NAMES = {
    "context": "Context",
    "policy": "Policy",
    "service_delivery": "Service Delivery",
    "human_resources": "HR",
    "supply_chain": "Supply Chain",
    "barriers": "Barriers",
}


def _fig_to_png(fig, width=800, height=500) -> bytes:
    """Convert a Plotly figure to PNG bytes."""
    try:
        return fig.to_image(format="png", width=width, height=height, scale=2)
    except Exception as e:
        logger.warning("Failed to convert chart to PNG (kaleido may not be installed): %s", e)
        return b""


def create_radar_chart(component_scores: dict) -> tuple:
    """Create a radar/spider chart showing % enablers per component.

    Args:
        component_scores: {component: {enabler_count, barrier_count}}

    Returns:
        (plotly_fig, png_bytes)
    """
    categories = []
    values = []

    for comp in COMPONENT_ORDER:
        data = component_scores.get(comp, {})
        enablers = data.get("enabler_count", 0)
        barriers = data.get("barrier_count", 0)
        total = enablers + barriers
        pct = (enablers / total * 100) if total > 0 else 0
        categories.append(COMPONENT_SHORT_NAMES.get(comp, comp))
        values.append(round(pct, 1))

    # Close the radar by repeating first value
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor=LIGHT_TEAL,
        line=dict(color=TEAL, width=2),
        name='% Enablers',
        text=[f"{v}%" for v in values_closed],
        textposition='top center',
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%"),
        ),
        title="Readiness Profile: % Enablers by Component",
        showlegend=False,
        height=500,
        margin=dict(t=60, b=40),
        font_family=CHART_FONT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig, _fig_to_png(fig)


def create_theme_heatmap(theme_data: dict) -> tuple:
    """Create a heatmap showing 11 themes x 6 components.

    Args:
        theme_data: {theme_name: {component: count}} or will be computed

    Returns:
        (plotly_fig, png_bytes)
    """
    themes = list(theme_data.keys())
    components = [COMPONENT_SHORT_NAMES.get(c, c) for c in COMPONENT_ORDER]

    z = []
    for theme in themes:
        row = []
        for comp in COMPONENT_ORDER:
            row.append(theme_data.get(theme, {}).get(comp, 0))
        z.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=components,
        y=themes,
        colorscale=[
            [0, "#FFFFFF"],
            [0.25, "#B2DFDB"],
            [0.5, "#4DB6AC"],
            [0.75, "#00897B"],
            [1, "#004D40"],
        ],
        text=z,
        texttemplate="%{text}",
        textfont={"size": 11},
        hoverongaps=False,
        colorbar=dict(title="Count"),
    ))

    fig.update_layout(
        title="Theme Distribution Across Components",
        xaxis_title="Component",
        yaxis_title="Theme",
        height=max(400, len(themes) * 35 + 100),
        margin=dict(l=250, t=60),
        yaxis=dict(autorange="reversed"),
        font_family=CHART_FONT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig, _fig_to_png(fig, width=900, height=max(400, len(themes) * 35 + 100))


def create_enabler_barrier_bar(components_data: list[dict]) -> tuple:
    """Create a grouped bar chart showing enablers vs barriers for all components.

    Args:
        components_data: [{name, enabler_count, barrier_count}]

    Returns:
        (plotly_fig, png_bytes)
    """
    names = [d["name"] for d in components_data]
    enablers = [d["enabler_count"] for d in components_data]
    barriers = [d["barrier_count"] for d in components_data]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Enablers',
        x=names,
        y=enablers,
        marker_color=TEAL,
        text=enablers,
        textposition='auto',
    ))
    fig.add_trace(go.Bar(
        name='Barriers',
        x=names,
        y=barriers,
        marker_color=RED,
        text=barriers,
        textposition='auto',
    ))

    fig.update_layout(
        barmode='group',
        title='Enablers vs Barriers by Component',
        height=400,
        xaxis_tickangle=-20,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=80),
        font_family=CHART_FONT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig, _fig_to_png(fig, width=900, height=400)


def create_component_bar(enablers: int, barriers: int, name: str) -> tuple:
    """Create a simple bar chart for a single component.

    Returns:
        (plotly_fig, png_bytes)
    """
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Enablers', 'Barriers'],
        y=[enablers, barriers],
        marker_color=[TEAL, RED],
        text=[enablers, barriers],
        textposition='auto',
    ))
    fig.update_layout(
        title=name,
        height=300,
        showlegend=False,
        margin=dict(t=40, b=20),
        font_family=CHART_FONT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig, _fig_to_png(fig, width=600, height=300)


def fig_from_json(fig_json: dict) -> go.Figure:
    """Reconstruct a Plotly figure from its JSON representation."""
    return go.Figure(fig_json)


def build_theme_data_from_analyses(component_analyses: list[dict]) -> dict:
    """Build theme_data dict from component analyses for heatmap.

    Args:
        component_analyses: List of component analysis dicts from DB

    Returns:
        {theme_name: {component: count}}
    """
    theme_data = {}
    for ca in component_analyses:
        comp = ca.get("component", "")
        for entry in ca.get("qualitative_entries", []):
            theme = entry.get("theme", "Other")
            if theme not in theme_data:
                theme_data[theme] = {}
            theme_data[theme][comp] = theme_data[theme].get(comp, 0) + 1
    return theme_data
