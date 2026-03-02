"""SEHRA Analyzer - Main Streamlit Application."""

import streamlit as st
import yaml
import streamlit_authenticator as stauth
from dotenv import load_dotenv
from core.db import init_db
from core.logging_config import setup_logging
from core.ui_theme import apply_theme, sidebar_branding

# Load environment variables from .env file
load_dotenv()

# Configure logging (stdout for Railway)
setup_logging()

# Initialize database on startup
init_db()

# Page configuration
st.set_page_config(
    page_title="SEHRA Analyzer",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply global theme
apply_theme()

# --- Share Token Routing (before auth) ---
token = st.query_params.get("token")
if token:
    from core.share_utils import render_public_report_view
    render_public_report_view(token)
    st.stop()

# --- Authentication ---
with open("auth_config.yaml") as f:
    auth_config = yaml.safe_load(f)

authenticator = stauth.Authenticate(
    auth_config["credentials"],
    auth_config["cookie"]["name"],
    auth_config["cookie"]["key"],
    auth_config["cookie"]["expiry_days"],
)

authenticator.login()

if st.session_state.get("authentication_status"):
    # Authenticated - show app
    with st.sidebar:
        sidebar_branding()
        st.write(f"Logged in as **{st.session_state.get('name', '')}**")
        authenticator.logout("Logout", "sidebar")

    # Navigation — 4 main pages + admin
    collect_page = st.Page("pages/1_collect.py", title="Collect Data", icon=":material/edit_note:")
    upload_page = st.Page("pages/2_upload.py", title="Upload PDF", icon=":material/upload_file:")
    dashboard_page = st.Page("pages/3_dashboard.py", title="Dashboard", icon=":material/dashboard:")
    export_page = st.Page("pages/4_export.py", title="Export & Share", icon=":material/ios_share:")

    pages = [collect_page, upload_page, dashboard_page, export_page]

    # Admin page (only for admin users)
    admin_page = st.Page("pages/admin_codebook.py", title="Manage Questions", icon=":material/settings:")
    pages.append(admin_page)

    pg = st.navigation(pages)
    pg.run()

elif st.session_state.get("authentication_status") is False:
    st.error("Username or password is incorrect")

elif st.session_state.get("authentication_status") is None:
    st.markdown("""
    <div style="display:flex;justify-content:center;align-items:center;min-height:40vh;margin-top:2rem;">
        <div style="
            text-align:center;
            background:rgba(255,255,255,0.8);
            backdrop-filter:blur(10px);
            -webkit-backdrop-filter:blur(10px);
            border:1px solid rgba(13,115,119,0.12);
            border-radius:16px;
            padding:48px 56px;
            box-shadow:0 4px 24px rgba(0,0,0,0.06);
            max-width:480px;
        ">
            <div style="font-size:2rem;font-weight:700;color:#0D7377;letter-spacing:0.06em;">SEHRA</div>
            <div style="font-size:0.85rem;color:#64748B;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:24px;">Analysis Platform</div>
            <p style="color:#1A1A2E;font-size:0.95rem;line-height:1.6;margin-bottom:8px;">
                Upload SEHRA PDFs or collect data via web forms, get automated quantitative
                and qualitative analysis, review results, chat with AI, and export reports.
            </p>
            <p style="color:#94A3B8;font-size:0.82rem;margin-top:16px;">
                Built for <strong>PRASHO Foundation</strong> by Samanvay Research and Development Foundation.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.info("Please log in to access the SEHRA Analyzer.")
