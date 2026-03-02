"""Centralized UI theme: CSS injection and reusable styled components."""

import streamlit as st

# Design tokens
TEAL = "#0D7377"
TEAL_DARK = "#095456"
RED = "#CC3333"
GRAY_50 = "#F5F7F9"
GRAY_100 = "#E8ECF0"
GRAY_400 = "#94A3B8"
GRAY_600 = "#64748B"
GRAY_900 = "#1A1A2E"
AMBER = "#D97706"
BLUE = "#2563EB"
GREEN = "#16A34A"

FONT_STACK = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"


def apply_theme():
    """Inject global CSS into the Streamlit app. Call once after set_page_config()."""
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Base typography ── */
    html, body, [class*="css"] {{
        font-family: {FONT_STACK};
    }}

    /* ── Hide Streamlit branding ── */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{
        background: rgba(255,255,255,0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid {GRAY_100};
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {TEAL_DARK} 0%, {TEAL} 100%);
    }}
    section[data-testid="stSidebar"] * {{
        color: #FFFFFF !important;
    }}
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stTextInput label {{
        color: rgba(255,255,255,0.8) !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: #FFFFFF !important;
    }}
    /* Sidebar nav links */
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {{
        color: rgba(255,255,255,0.85) !important;
        border-radius: 8px;
        margin: 2px 0;
        transition: background 0.2s;
    }}
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover {{
        background: rgba(255,255,255,0.12) !important;
    }}
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] {{
        background: rgba(255,255,255,0.18) !important;
        color: #FFFFFF !important;
        font-weight: 600;
    }}
    /* Sidebar nav separator lines */
    section[data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,0.15) !important;
    }}
    /* Sidebar button (logout) */
    section[data-testid="stSidebar"] button {{
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }}
    section[data-testid="stSidebar"] button:hover {{
        background: rgba(255,255,255,0.2) !important;
    }}

    /* ── Buttons ── */
    .stButton > button[kind="primary"],
    button[data-testid="stBaseButton-primary"] {{
        background: linear-gradient(135deg, {TEAL} 0%, {TEAL_DARK} 100%);
        border: none;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.01em;
        transition: transform 0.15s, box-shadow 0.15s;
    }}
    .stButton > button[kind="primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(13,115,119,0.35);
    }}
    .stButton > button[kind="secondary"],
    button[data-testid="stBaseButton-secondary"] {{
        border-radius: 8px;
        font-weight: 500;
        border: 1px solid {GRAY_100};
        transition: transform 0.15s;
    }}
    .stButton > button[kind="secondary"]:hover,
    button[data-testid="stBaseButton-secondary"]:hover {{
        transform: translateY(-1px);
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        border-bottom: 2px solid {GRAY_100};
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 500;
        color: {GRAY_600};
    }}
    .stTabs [aria-selected="true"] {{
        border-bottom: 3px solid {TEAL} !important;
        color: {TEAL} !important;
        font-weight: 600;
    }}

    /* ── Inputs ── */
    .stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"],
    .stNumberInput input {{
        border-radius: 8px !important;
        border-color: {GRAY_100} !important;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: {TEAL} !important;
        box-shadow: 0 0 0 1px {TEAL} !important;
    }}

    /* ── File uploader ── */
    [data-testid="stFileUploader"] section {{
        border: 2px dashed {GRAY_100};
        border-radius: 12px;
        padding: 24px;
        transition: border-color 0.2s, background 0.2s;
    }}
    [data-testid="stFileUploader"] section:hover {{
        border-color: {TEAL};
        background: rgba(13,115,119,0.03);
    }}

    /* ── Metric cards ── */
    [data-testid="stMetric"] {{
        background: #FFFFFF;
        border: 1px solid {GRAY_100};
        border-left: 4px solid {TEAL};
        border-radius: 8px;
        padding: 12px 16px;
    }}

    /* ── Expanders ── */
    [data-testid="stExpander"] {{
        border: 1px solid {GRAY_100};
        border-radius: 10px;
        overflow: hidden;
    }}
    [data-testid="stExpander"] summary {{
        font-weight: 500;
    }}

    /* ── Containers ── */
    [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
    }}

    /* ── Chat messages ── */
    [data-testid="stChatMessage"] {{
        border-radius: 12px;
        border: 1px solid {GRAY_100};
    }}

    /* ── Progress bar ── */
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, {TEAL} 0%, {TEAL_DARK} 100%);
        border-radius: 8px;
    }}

    /* ── Download button ── */
    .stDownloadButton > button {{
        border-radius: 8px !important;
    }}

    /* ── Dataframe ── */
    .stDataFrame {{
        border-radius: 8px;
        overflow: hidden;
    }}
    </style>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    """Render a clean page header with optional subtitle."""
    html = f'<h1 style="margin-bottom:0;color:{GRAY_900};font-weight:700;">{title}</h1>'
    if subtitle:
        html += f'<p style="color:{GRAY_600};margin-top:4px;margin-bottom:24px;font-size:1.05rem;">{subtitle}</p>'
    else:
        html += '<div style="margin-bottom:20px;"></div>'
    st.markdown(html, unsafe_allow_html=True)


def kpi_card(value, label: str, color: str = TEAL, prefix: str = "", suffix: str = ""):
    """Render a glassmorphism KPI card with colored left border."""
    display_val = f"{prefix}{value}{suffix}"
    st.markdown(f"""
    <div style="
        background: rgba(255,255,255,0.7);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.5);
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    ">
        <div style="font-size:2.2em;font-weight:700;color:{color};line-height:1.2;">{display_val}</div>
        <div style="font-size:0.85em;color:{GRAY_600};margin-top:4px;font-weight:500;text-transform:uppercase;letter-spacing:0.05em;">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str, description: str = ""):
    """Render a section header with teal left-border accent."""
    html = f"""
    <div style="border-left:3px solid {TEAL};padding-left:12px;margin:28px 0 16px 0;">
        <h3 style="margin:0;color:{GRAY_900};font-weight:600;font-size:1.25rem;">{title}</h3>
    """
    if description:
        html += f'<p style="margin:2px 0 0 0;color:{GRAY_600};font-size:0.9rem;">{description}</p>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def status_badge(status: str):
    """Render a pill-shaped status badge."""
    color_map = {
        "draft": (AMBER, "#FFFBEB"),
        "reviewed": (BLUE, "#EFF6FF"),
        "published": (GREEN, "#F0FDF4"),
    }
    fg, bg = color_map.get(status.lower(), (GRAY_600, GRAY_50))
    st.markdown(f"""
    <span style="
        display:inline-block;
        background:{bg};
        color:{fg};
        padding:4px 14px;
        border-radius:999px;
        font-size:0.82rem;
        font-weight:600;
        letter-spacing:0.02em;
        text-transform:capitalize;
        border: 1px solid {fg}22;
    ">{status}</span>
    """, unsafe_allow_html=True)


def step_indicator(steps: list[dict], current: int):
    """Render a horizontal stepper with numbered circles and connecting lines.

    Args:
        steps: list of {"title": str} dicts
        current: 0-based index of the active step
    """
    items_html = ""
    for i, step in enumerate(steps):
        if i < current:
            # completed
            circle_style = f"background:{TEAL};color:#fff;border:2px solid {TEAL};"
            label_style = f"color:{TEAL};font-weight:600;"
            number = "&#10003;"
        elif i == current:
            # active
            circle_style = f"background:#fff;color:{TEAL};border:2px solid {TEAL};font-weight:700;"
            label_style = f"color:{TEAL};font-weight:600;"
            number = str(i + 1)
        else:
            # upcoming
            circle_style = f"background:#fff;color:{GRAY_400};border:2px solid {GRAY_100};"
            label_style = f"color:{GRAY_400};"
            number = str(i + 1)

        line_html = ""
        if i < len(steps) - 1:
            line_color = TEAL if i < current else GRAY_100
            line_html = f'<div style="flex:1;height:2px;background:{line_color};margin:0 4px;align-self:center;"></div>'

        items_html += f"""
        <div style="display:flex;flex-direction:column;align-items:center;min-width:0;">
            <div style="width:32px;height:32px;border-radius:50%;{circle_style}display:flex;align-items:center;justify-content:center;font-size:0.85rem;flex-shrink:0;">
                {number}
            </div>
            <div style="font-size:0.7rem;margin-top:4px;text-align:center;{label_style}white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:80px;">
                {step["title"]}
            </div>
        </div>
        {line_html}
        """

    st.markdown(f"""
    <div style="display:flex;align-items:flex-start;gap:0;margin:12px 0 20px 0;overflow-x:auto;">
        {items_html}
    </div>
    """, unsafe_allow_html=True)


def export_card(format_name: str, description: str, icon: str):
    """Render a centered card for export options.

    Args:
        icon: A short string (1-2 chars) displayed in a teal circle.
    """
    st.markdown(f"""
    <div style="text-align:center;padding:16px 12px 8px 12px;">
        <div style="
            display:inline-flex;align-items:center;justify-content:center;
            width:48px;height:48px;border-radius:50%;
            background:linear-gradient(135deg, {TEAL} 0%, {TEAL_DARK} 100%);
            color:#fff;font-weight:700;font-size:1.1rem;margin-bottom:8px;
        ">{icon}</div>
        <div style="font-weight:600;font-size:1rem;color:{GRAY_900};">{format_name}</div>
        <div style="font-size:0.8rem;color:{GRAY_600};margin-top:2px;">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def sidebar_branding():
    """Render 'SEHRA / ANALYSIS PLATFORM' header in sidebar."""
    st.markdown(f"""
    <div style="padding:8px 0 16px 0;margin-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.15);">
        <div style="font-size:1.5rem;font-weight:700;letter-spacing:0.08em;color:#FFFFFF;">SEHRA</div>
        <div style="font-size:0.7rem;font-weight:500;letter-spacing:0.15em;color:rgba(255,255,255,0.7);text-transform:uppercase;">Analysis Platform</div>
    </div>
    """, unsafe_allow_html=True)


def metric_row(metrics: list[dict]):
    """Render a compact inline metric row.

    Args:
        metrics: [{"label": str, "value": str|int, "color": str (optional)}]
    """
    items = ""
    for m in metrics:
        color = m.get("color", GRAY_900)
        items += f"""
        <div style="text-align:center;padding:0 16px;">
            <div style="font-size:1.4em;font-weight:700;color:{color};">{m["value"]}</div>
            <div style="font-size:0.75rem;color:{GRAY_600};text-transform:uppercase;letter-spacing:0.05em;">{m["label"]}</div>
        </div>
        """
    st.markdown(f"""
    <div style="display:flex;justify-content:flex-start;gap:8px;padding:8px 0;flex-wrap:wrap;">
        {items}
    </div>
    """, unsafe_allow_html=True)


def apply_plotly_theme(fig):
    """Apply consistent font and transparent background to a Plotly figure."""
    fig.update_layout(
        font_family=FONT_STACK,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
