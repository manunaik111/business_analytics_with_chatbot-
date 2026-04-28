# main_app.py
# Team 5 — Integration & Interface
# Midnight Aurora theme + Team 4 layout + All modules integrated

import streamlit as st
from streamlit_float import *
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os, time

sys.path.append(os.path.dirname(__file__))

# ── Team 1 ────────────────────────────────────────────────────────────────
from data_management.file_upload import file_upload_section
from data_management.dataset_profiling import dataset_profiling_section
from data_management.data_quality import data_quality_section

# ── Team 2 ────────────────────────────────────────────────────────────────
from nlp.nlp_processor import process_query
from nlp.data_processor import execute_query
from nlp.response_generator import generate_response
from nlp.voice_input import transcribe_voice
from nlp.voice_output import speak

# ── Team 3 ────────────────────────────────────────────────────────────────
from analytics.analysis import RetailDataAnalyzer
from analytics.insights import generate_ai_insights
from analytics.my_recommendations import generate_smart_recommendations
from analytics.predictive_engine import SalesPredictiveEngine

# ── Team 4 ────────────────────────────────────────────────────────────────
from dashboard import utils as dash_utils
from dashboard.data_ingestion import load_file
from dashboard.data_cleaning import clean_data
from dashboard.data_analysis import get_column_types, find_correlations, compute_stats
from dashboard.kpi_generator import generate_kpis
from dashboard.visualization import auto_charts
from dashboard.insights import generate_insights

# ── Team 5 ────────────────────────────────────────────────────────────────
from chatbot.chatbot_engine import chat, clear_memory, initialize_memory, get_analyzer
from report_generator import generate_report_pdf, generate_report_excel
from auth import (
    init_db, init_session, is_authenticated, current_user,
    logout_user, can, show_landing_page, show_login_page,
    show_register_page, show_user_management,
    PERM_VIEW_DASHBOARD, PERM_VIEW_RAW_DATA, PERM_USE_CHATBOT,
    PERM_DOWNLOAD_EXCEL, PERM_DOWNLOAD_PDF, PERM_MANAGE_USERS,
    PERM_VIEW_AI_INSIGHTS, PERM_VIEW_ALL_CHARTS,
    ROLE_COLORS,
    show_skeleton_kpi, show_skeleton_chart, show_progress_bar,
    show_inline_spinner, wrap_page_fade
)

# ══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': "AI Sales Analytics Dashboard"}
)

init_db()
init_session()

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'

if not is_authenticated():
    page = st.session_state.current_page
    if page == 'login':        show_login_page()
    elif page == 'register':   show_register_page()
    else:                      show_landing_page()
    st.stop()

float_init()
initialize_memory()
wrap_page_fade()

# ── Session state defaults ────────────────────────────────────────────────
for k, v in [
    ('chat_open', False), ('pending_q', None),
    ('app_loaded', False), ('api_error', None),
    ('uploaded_df', None), ('chat_messages', []),
    ('module_page', 'Dashboard'),
]:
    if k not in st.session_state:
        st.session_state[k] = v

st.session_state.current_page = 'dashboard'

# ══════════════════════════════════════════════════════════════════════════
# MIDNIGHT AURORA CSS
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

#MainMenu {visibility: hidden;}
footer    {visibility: hidden;}
* { font-family: 'Inter', sans-serif !important; }
.material-icons,.material-symbols-outlined,.material-symbols-rounded,.material-symbols-sharp {
    font-family: "Material Symbols Rounded","Material Symbols Outlined","Material Icons",sans-serif !important;
}
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary svg,
[data-testid="stExpanderToggleIcon"] {
    font-family: "Material Symbols Rounded","Material Icons",sans-serif !important;
}

.stApp {
    background-color: #080B14 !important;
    background-image:
        radial-gradient(ellipse at 15% 15%, rgba(123,47,190,0.07) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 85%, rgba(0,212,255,0.04) 0%, transparent 55%);
}
.block-container { padding-top: 0.5rem !important; padding-bottom: 3rem !important; max-width: 100% !important; }
h1,h2,h3,p,span,div,label { color: #E0E0E0 !important; }

@keyframes gradientShift {
    0%   { background-position: 0% 50%;   }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%;   }
}
.animated-title {
    background: linear-gradient(270deg, #00D4FF, #C084FC, #818CF8, #38BDF8, #00D4FF);
    background-size: 400% 400%;
    animation: gradientShift 6s ease infinite;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    font-size: 2.6rem; font-weight: 900; letter-spacing: -1.5px;
    text-align: center; margin: 0; line-height: 1.15;
}
.title-sub {
    color: #4B5563 !important; font-size: 12px; text-align: center;
    letter-spacing: 3px; text-transform: uppercase; margin-top: 8px; font-weight: 500;
}
.topbar-breadcrumb {
    font-size: 11px; color: #4B5563 !important; margin-top: 4px; letter-spacing: 0.5px;
}
.glow-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, rgba(123,47,190,0.9) 25%, rgba(0,212,255,0.9) 50%, rgba(123,47,190,0.9) 75%, transparent 100%);
    margin: 1.6rem 0; border: none;
    box-shadow: 0 0 10px rgba(123,47,190,0.35), 0 0 20px rgba(0,212,255,0.15);
}
.fade-long-line {
    width: 100%; height: 1px; margin: 18px 0 14px 0;
    background: linear-gradient(90deg, rgba(123,47,190,0) 0%, rgba(123,47,190,0.65) 20%, rgba(0,212,255,0.55) 50%, rgba(123,47,190,0.65) 80%, rgba(123,47,190,0) 100%);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A0A1A 0%, #0F0F22 100%) !important;
    border-right: 1px solid rgba(123,47,190,0.25) !important;
}
[data-testid="stSidebar"] * { color: #E0E0E0 !important; }
[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #1A1A30 !important; color: white !important;
    border: 1px solid rgba(123,47,190,0.4) !important; border-radius: 8px !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] * { color: white !important; }
div[data-baseweb="popover"] div[data-baseweb="menu"] { background-color: #1A1A30 !important; }
div[data-baseweb="popover"] div[data-baseweb="menu"] li { color: white !important; background-color: #1A1A30 !important; }
div[data-baseweb="popover"] div[data-baseweb="menu"] li:hover { background-color: #2A2A45 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #7B2FBE, #5B21B6) !important;
    color: white !important; border-radius: 10px !important; border: none !important;
    width: 100% !important; font-weight: 700 !important;
    box-shadow: 0 0 15px rgba(123,47,190,0.35) !important; transition: all 0.2s ease !important;
}

/* KPI Cards */
.kpi-card {
    background: rgba(18,18,35,0.75); backdrop-filter: blur(24px);
    border-radius: 18px; border: 1px solid rgba(123,47,190,0.22);
    box-shadow: 0 8px 32px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.04);
    overflow: hidden; transition: transform 0.25s ease, box-shadow 0.25s ease; margin-bottom: 0.5rem;
}
.kpi-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 48px rgba(0,0,0,0.55), 0 0 24px rgba(123,47,190,0.35);
    border-color: rgba(123,47,190,0.55);
}
.kpi-top-bar { height: 3px; width: 100%; }
.kpi-body { padding: 10px 10px 12px 10px; display: flex; flex-direction: column; gap: 4px; }
.kpi-label { font-size: 9px !important; color: #6B7280 !important; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 700; }
.kpi-value { font-size: 1.6rem !important; font-weight: 900 !important; line-height: 1.1; margin-bottom: 0; }

/* Section titles */
.section-title {
    display: flex; align-items: center; gap: 10px;
    font-size: 10px !important; font-weight: 700 !important;
    color: #4B5563 !important; text-transform: uppercase; letter-spacing: 2.5px; margin: 28px 0 14px 0;
}
.section-title::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(123,47,190,0.6), transparent); }

/* Chart cards */
.chart-card {
    background: rgba(12,12,28,0.8); backdrop-filter: blur(24px);
    border-radius: 18px; padding: 16px; border: 1px solid rgba(123,47,190,0.18);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.02);
    margin-bottom: 14px; transition: border-color 0.25s ease;
}
.chart-card:hover { border-color: rgba(123,47,190,0.38); }
.chart-label { font-size: 10px; font-weight: 700; color: #6B7280 !important; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid rgba(123,47,190,0.15); }

/* Insight cards */
.insight-card {
    background: rgba(12,12,28,0.8); backdrop-filter: blur(20px);
    border-radius: 14px; padding: 16px; border-top: 3px solid transparent;
    box-shadow: 0 8px 28px rgba(0,0,0,0.35); transition: transform 0.2s ease; height: 100%;
}
.insight-card:hover { transform: translateY(-3px); }

/* Rec card */
.rec-card {
    background: rgba(18,18,35,0.75); border: 1px solid rgba(123,47,190,0.15);
    border-radius: 10px; padding: 10px 14px; margin-bottom: 6px;
    font-size: 12px; color: #D1D5DB !important; line-height: 1.5;
}

/* Activity feed */
.act-item {
    display: flex; gap: 9px; padding: 7px 0;
    border-bottom: 1px solid rgba(123,47,190,0.08);
    font-size: 11px; color: rgba(255,255,255,0.65) !important;
}

/* Download buttons */
.stDownloadButton > button {
    border-radius: 10px !important; font-weight: 600 !important;
    border: 1px solid rgba(123,47,190,0.45) !important;
    background: rgba(123,47,190,0.15) !important; color: #C084FC !important;
    backdrop-filter: blur(10px) !important; transition: all 0.2s ease !important;
}

/* Primary / Secondary buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#7B2FBE,#5B21B6) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; box-shadow: 0 0 14px rgba(123,47,190,0.32) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(18,18,35,0.7) !important; color: #C084FC !important;
    border: 1px solid rgba(123,47,190,0.38) !important; border-radius: 10px !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: rgba(12,12,28,0.8) !important; backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(123,47,190,0.22) !important; border-radius: 14px !important;
}

/* Chat */
.msg-user {
    background: linear-gradient(135deg,rgba(123,47,190,0.85),rgba(91,33,182,0.85));
    color: white; padding: 10px 15px; border-radius: 16px 16px 3px 16px; margin: 6px 0;
    font-size: 13px; word-wrap: break-word; text-align: right; line-height: 1.5;
}
.msg-bot {
    background: rgba(18,18,35,0.85); color: #E0E0E0; padding: 10px 15px;
    border-radius: 16px 16px 16px 3px; margin: 6px 0;
    font-size: 13px; word-wrap: break-word; border: 1px solid rgba(123,47,190,0.2); line-height: 1.5;
}
.chat-header {
    background: linear-gradient(135deg,#7B2FBE,#5B21B6); color: white;
    padding: 14px 18px; border-radius: 14px 14px 0 0; font-weight: 700; font-size: 15px; margin-bottom: 10px;
}
div[data-testid="stChatInput"] > div {
    border-radius: 12px !important; border: 1px solid rgba(123,47,190,0.38) !important;
    background: rgba(18,18,35,0.85) !important; backdrop-filter: blur(10px) !important;
}

/* Alert */
div[data-testid="stAlert"] {
    background: rgba(18,18,35,0.75) !important; border: 1px solid rgba(123,47,190,0.28) !important;
    border-radius: 12px !important; backdrop-filter: blur(10px) !important;
}

/* Quick analysis box */
.quick-box { background: rgba(18,18,35,0.75); backdrop-filter: blur(16px); border-radius: 14px; padding: 14px 16px; border: 1px solid rgba(123,47,190,0.2); margin-top: 8px; }
.quick-row { padding: 7px 0; border-bottom: 1px solid rgba(123,47,190,0.1); font-size: 13px; color: #D1D5DB !important; }
.quick-row:last-child { border-bottom: none; }
.quick-label { font-size: 10px; font-weight: 700; color: #6B7280 !important; text-transform: uppercase; letter-spacing: 1px; }

/* Prog bars */
.prog-track { height: 5px; border-radius: 3px; background: rgba(255,255,255,0.07); margin-bottom: 10px; }
.prog-fill  { height: 100%; border-radius: 3px; }

[data-testid="stHorizontalBlock"] { gap: 8px !important; }
[data-testid="column"] { min-width: 80px !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# DATA HELPERS
# ══════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    analyzer = get_analyzer()
    df = analyzer.df.copy()
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, errors="coerce")
    df["Ship Date"]  = pd.to_datetime(df["Ship Date"],  dayfirst=True, errors="coerce")
    if "shipping_delay_days" not in df.columns:
        df["shipping_delay_days"] = (df["Ship Date"] - df["Order Date"]).dt.days.fillna(0)
    df["Year"]     = df["Order Date"].dt.year
    df["Month"]    = df["Order Date"].dt.to_period("M")
    df["MonthStr"] = df["Month"].astype(str)
    for col in ["Category", "Region"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")
    return df

def get_active_df():
    """Returns uploaded df if available, else default dataset."""
    if st.session_state.get("uploaded_df") is not None:
        return st.session_state["uploaded_df"]
    return df

def apply_filters(df, cat, region, year, profit):
    f = df.copy()
    if cat    != "All" and "Category" in f.columns: f = f[f["Category"] == cat]
    if region != "All" and "Region"   in f.columns: f = f[f["Region"]   == region]
    if year   != "All" and "Year"     in f.columns: f = f[f["Year"]     == int(year)]
    if profit == "Profitable"  and "Profit" in f.columns: f = f[f["Profit"] > 0]
    elif profit == "Loss Making" and "Profit" in f.columns: f = f[f["Profit"] < 0]
    return f

def compute_kpis(df):
    if df.empty: return {}
    total_sales = df["Sales"].sum() if "Sales" in df.columns else 0
    total_profit = df["Profit"].sum() if "Profit" in df.columns else 0
    return {
        "total_sales":   total_sales,
        "avg_order":     df["Sales"].mean() if "Sales" in df.columns else 0,
        "total_profit":  total_profit,
        "profit_margin": (df["Profit"]/df["Sales"]).mean()*100 if total_sales else 0,
        "profit_ratio":  (total_profit/total_sales)*100 if total_sales else 0,
        "avg_discount":  df["Discount"].mean()*100 if "Discount" in df.columns else 0,
        "avg_shipping":  df["shipping_delay_days"].mean() if "shipping_delay_days" in df.columns else 0,
        "total_records": len(df),
    }

def fmt(v, pre='', suf='', dec=0):
    if isinstance(v, (int, float)): return f"{pre}{v:,.{dec}f}{suf}"
    return str(v)

def mini_line(df, metric="Sales"):
    if df.empty or metric not in df.columns: return go.Figure()
    monthly = df.groupby(df["Order Date"].dt.to_period("M"))[metric].sum().reset_index()
    monthly["Date"] = monthly["Order Date"].dt.start_time
    fig = px.line(monthly, x="Date", y=metric, line_shape="spline")
    fig.update_layout(width=200, height=32, margin=dict(l=0,r=0,t=0,b=0),
                      xaxis_visible=False, yaxis_visible=False,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    fig.update_traces(line=dict(color="#C084FC", width=1.5))
    return fig

# ── Load default data ─────────────────────────────────────────────────────
try:
    df = load_data()
    dataset_loaded = True
except Exception as e:
    dataset_loaded = False
    df = pd.DataFrame()

# ══════════════════════════════════════════════════════════════════════════
# PENDING CHAT QUESTION
# ══════════════════════════════════════════════════════════════════════════
if st.session_state.pending_q:
    question = st.session_state.pending_q
    st.session_state.pending_q = None
    st.session_state.chat_messages.append({'role': 'user', 'content': question})
    with st.spinner(""):
        try:
            parsed   = process_query(question)
            active   = get_active_df()
            result   = execute_query(active, parsed) if active is not None else {"data": None}
            nlp_resp = generate_response(parsed, result)
        except Exception:
            nlp_resp = None
        response = chat(question) if not nlp_resp or nlp_resp.startswith("Sorry") else nlp_resp
    if response:
        st.session_state.chat_messages.append({'role': 'assistant', 'content': response})
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════
# STARTUP LOADING SCREEN
# ══════════════════════════════════════════════════════════════════════════
if not st.session_state.app_loaded:
    wrap_page_fade()
    show_progress_bar()
    show_skeleton_kpi(4)
    st.markdown("<br>", unsafe_allow_html=True)
    show_skeleton_chart(300)
    slot = show_inline_spinner("Initialising dashboard…")
    try:
        analyzer = get_analyzer()
        time.sleep(0.8)
        slot.empty()
        st.session_state.app_loaded = True
        st.rerun()
    except Exception as e:
        slot.empty()
        st.session_state.app_loaded = True
        st.session_state.api_error  = str(e)
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════
PAGES = ["Dashboard", "Visualization", "Predictive Analytics",
         "Data Upload", "Dataset Profiling", "Data Quality",
         "Meet Our Team", "Settings"]

with st.sidebar:
    # Brand
    st.markdown("""
    <div style="display:flex;align-items:center;gap:9px;padding:4px 0 14px">
      <div style="width:30px;height:30px;border-radius:8px;
                  background:linear-gradient(135deg,#7B2FBE,#5B21B6);
                  display:flex;align-items:center;justify-content:center;font-size:16px">📊</div>
      <div>
        <div style="font-size:14px;font-weight:600;color:rgba(255,255,255,0.92)">Sales Analytics</div>
        <div style="font-size:9px;color:rgba(255,255,255,0.3);text-transform:uppercase;letter-spacing:.07em">AI Dashboard</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.divider()

    # Dashboards nav group
    st.markdown('<div style="font-size:9px;font-weight:600;color:rgba(255,255,255,0.28);text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px">Dashboards</div>', unsafe_allow_html=True)
    for p in ["Dashboard", "Visualization", "Predictive Analytics"]:
        icons = {"Dashboard": "📊", "Visualization": "📈", "Predictive Analytics": "🔮"}
        is_on = st.session_state.module_page == p
        if st.button(f"{icons[p]}  {p}", key=f"nav_{p}", use_container_width=True,
                     type="primary" if is_on else "secondary"):
            st.session_state.module_page = p; st.rerun()

    st.divider()

    # Data nav group
    st.markdown('<div style="font-size:9px;font-weight:600;color:rgba(255,255,255,0.28);text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px">Data</div>', unsafe_allow_html=True)
    for p in ["Data Upload", "Dataset Profiling", "Data Quality"]:
        icons2 = {"Data Upload": "📁", "Dataset Profiling": "📋", "Data Quality": "🔍"}
        is_on = st.session_state.module_page == p
        if st.button(f"{icons2[p]}  {p}", key=f"nav_{p}", use_container_width=True,
                     type="primary" if is_on else "secondary"):
            st.session_state.module_page = p; st.rerun()

    st.divider()

    # Filters (only on Dashboard page when data loaded)
    if st.session_state.module_page == "Dashboard" and dataset_loaded and not df.empty:
        st.markdown('<div style="font-size:9px;font-weight:600;color:rgba(255,255,255,0.28);text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px">Filters</div>', unsafe_allow_html=True)
        years = sorted(df["Year"].dropna().unique().astype(int).tolist())
        for k, v in [("year","All"),("category","All"),("region","All"),("profit_status","All")]:
            if k not in st.session_state: st.session_state[k] = v

        sel_cat    = st.selectbox("Category",      ["All"]+sorted(df["Category"].unique()), key="category")
        sel_region = st.selectbox("Region",        ["All"]+sorted(df["Region"].unique()),   key="region")
        sel_profit = st.selectbox("Profit Status", ["All","Profitable","Loss Making"],       key="profit_status")
        sel_year   = st.selectbox("Year",          ["All"]+[str(y) for y in years],         key="year")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Reset All Filters", type="primary"):
            for k in ["category","region","profit_status","year"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

        filtered_df = apply_filters(df, sel_cat, sel_region, sel_year, sel_profit)

        # Quick analysis
        if not filtered_df.empty:
            st.divider()
            st.markdown('<div style="font-size:10px;font-weight:700;color:#4B5563;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;">Quick Analysis</div>', unsafe_allow_html=True)
            try:
                best_cat   = filtered_df.groupby("Category")["Sales"].sum().idxmax()
                top_region = filtered_df.groupby("Region")["Sales"].sum().idxmax()
                best_profit= filtered_df.groupby("Category")["Profit"].sum().idxmax()
                filtered_df["MonthYear"] = filtered_df["Order Date"].dt.strftime("%b %Y")
                peak_month = filtered_df.groupby("MonthYear")["Sales"].sum().idxmax()
                st.markdown(f"""
                <div class="quick-box">
                    <div class="quick-row"><div class="quick-label">Best Category</div><div style="color:#C084FC;font-weight:600">{best_cat}</div></div>
                    <div class="quick-row"><div class="quick-label">Top Region</div><div style="color:#38BDF8;font-weight:600">{top_region}</div></div>
                    <div class="quick-row"><div class="quick-label">Highest Profit</div><div style="color:#86EFAC;font-weight:600">{best_profit}</div></div>
                    <div class="quick-row"><div class="quick-label">Peak Month</div><div style="color:#FCD34D;font-weight:600">{peak_month}</div></div>
                </div>""", unsafe_allow_html=True)
            except Exception:
                pass
    else:
        filtered_df = df.copy() if dataset_loaded else pd.DataFrame()
        sel_cat = sel_region = sel_year = sel_profit = "All"

    st.divider()

    # General nav
    for p in ["Meet Our Team", "Settings"]:
        icons3 = {"Meet Our Team": "👥", "Settings": "⚙️"}
        is_on = st.session_state.module_page == p
        if st.button(f"{icons3[p]}  {p}", key=f"nav_{p}", use_container_width=True,
                     type="primary" if is_on else "secondary"):
            st.session_state.module_page = p; st.rerun()

    st.divider()

    # User card
    user = current_user()
    role_color = ROLE_COLORS.get(user['role'], '#6B7280')
    st.markdown(f"""
    <div style="background:rgba(18,18,40,0.8);border-radius:12px;border:1px solid rgba(123,47,190,0.25);padding:14px 16px;margin-bottom:10px">
      <div style="font-size:11px;color:#6B7280;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">Logged in as</div>
      <div style="font-size:14px;font-weight:700;color:#E0E0E0">{user['full_name']}</div>
      <div style="font-size:11px;color:#9CA3AF;margin-bottom:8px">{user['email']}</div>
      <span style="background:{role_color}22;color:{role_color};border:1px solid {role_color}55;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:700">{user['role']}</span>
    </div>""", unsafe_allow_html=True)

    if st.button("Sign Out", key="logout_btn"):
        logout_user(); st.rerun()

    if can(PERM_MANAGE_USERS):
        st.markdown("---")
        if st.button("Manage Users", key="manage_users_btn"):
            st.session_state.show_user_mgmt = True

    st.caption("AI Sales Analytics  |  Genesis Training")

# ══════════════════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════════════════
page = st.session_state.module_page
page_icons = {"Dashboard":"📊","Visualization":"📈","Predictive Analytics":"🔮",
              "Data Upload":"📁","Dataset Profiling":"📋","Data Quality":"🔍",
              "Meet Our Team":"👥","Settings":"⚙️"}

col_title, col_rpt = st.columns([5, 2])
with col_title:
    active = get_active_df()
    fname  = f"· {len(active):,} rows × {len(active.columns)} cols" if active is not None and not active.empty else ""
    st.markdown(f"""
    <div style="padding:2px 0 10px">
      <div style="font-size:18px;font-weight:600;color:#C084FC">{page_icons.get(page,'')} {page}</div>
      <div class="topbar-breadcrumb">Home › {page} {fname}</div>
    </div>""", unsafe_allow_html=True)

with col_rpt:
    if page in ("Dashboard", "Visualization", "Predictive Analytics") and dataset_loaded:
        with st.expander("Download Report", expanded=False):
            rtype = st.radio("Format", ["PDF", "Excel"], horizontal=True, key="rpt_fmt")
            if st.button("Generate", key="gen_rpt", type="primary", use_container_width=True):
                try:
                    analyzer_obj = get_analyzer()
                    active = get_active_df()
                    from dashboard.data_analysis import get_column_types
                    from dashboard.kpi_generator import generate_kpis
                    col_types = get_column_types(active) if active is not None else {}
                    kpis = generate_kpis(active, col_types) if active is not None else []
                    if rtype == "Excel":
                        data = generate_report_excel(active, kpis, [], None, "")
                        st.download_button("Download Excel", data=data,
                                            file_name="sales_report.xlsx",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    else:
                        data = generate_report_pdf(active, kpis, [], None, "", [])
                        st.download_button("Download PDF", data=data,
                                         file_name="sales_report.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"Report error: {e}")

st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    if not dataset_loaded or filtered_df.empty:
        show_skeleton_kpi(4)
        st.info("No data loaded. Go to Data Upload to upload a dataset.")
    else:
        if can(PERM_VIEW_DASHBOARD):
            kpis = compute_kpis(filtered_df)

            # ── KPI Row 1 ──────────────────────────────────────────────────
            st.markdown('<div class="section-title">Key Performance Indicators</div>', unsafe_allow_html=True)
            kpi_data = [
                ("Total Sales",    fmt(kpis.get("total_sales",0),   pre="$"),          "Sales",               "linear-gradient(90deg,#C084FC,#818CF8)"),
                ("Avg Order Value",fmt(kpis.get("avg_order",0),     pre="$", dec=2),   "Sales",               "linear-gradient(90deg,#38BDF8,#0EA5E9)"),
                ("Total Profit",   fmt(kpis.get("total_profit",0),  pre="$"),          "Profit",              "linear-gradient(90deg,#86EFAC,#22C55E)"),
                ("Profit Margin",  fmt(kpis.get("profit_margin",0), suf="%", dec=1),   "Profit",              "linear-gradient(90deg,#FCD34D,#F59E0B)"),
                ("Profit Ratio",   fmt(kpis.get("profit_ratio",0),  suf="%", dec=1),   "Profit",              "linear-gradient(90deg,#F9A8D4,#EC4899)"),
                ("Avg Discount",   fmt(kpis.get("avg_discount",0),  suf="%", dec=1),   "Discount",            "linear-gradient(90deg,#FCA5A5,#EF4444)"),
                ("Avg Shipping",   fmt(kpis.get("avg_shipping",0),  suf=" days",dec=0),"shipping_delay_days", "linear-gradient(90deg,#6EE7B7,#10B981)"),
                ("Total Records",  fmt(kpis.get("total_records",0)),                   "Sales",               "linear-gradient(90deg,#C4B5FD,#7C3AED)"),
            ]
            row1 = st.columns(4, gap="medium")
            for i in range(4):
                label, value, spark_col, grad = kpi_data[i]
                with row1[i]:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-top-bar" style="background:{grad};"></div>
                        <div class="kpi-body">
                            <div class="kpi-label">{label}</div>
                            <div class="kpi-value" style="background:{grad};-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{value}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                    if spark_col in filtered_df.columns:
                        st.plotly_chart(mini_line(filtered_df, spark_col), use_container_width=True,
                                        config={'displayModeBar': False}, key=f"spark_{i}")

            st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
            row2 = st.columns(4, gap="medium")
            for i in range(4, 8):
                label, value, spark_col, grad = kpi_data[i]
                with row2[i-4]:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-top-bar" style="background:{grad};"></div>
                        <div class="kpi-body">
                            <div class="kpi-label">{label}</div>
                            <div class="kpi-value" style="background:{grad};-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{value}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                    if spark_col in filtered_df.columns:
                        st.plotly_chart(mini_line(filtered_df, spark_col), use_container_width=True,
                                        config={'displayModeBar': False}, key=f"spark_{i}")

        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

        # ── AI Insights ────────────────────────────────────────────────────
        if can(PERM_VIEW_AI_INSIGHTS):
            st.markdown('<div class="section-title">AI-Powered Insights</div>', unsafe_allow_html=True)
            try:
                best_cat     = filtered_df.groupby("Category")["Sales"].sum().idxmax()
                best_cat_val = filtered_df.groupby("Category")["Sales"].sum().max()
                best_region  = filtered_df.groupby("Region")["Profit"].sum().idxmax()
                filtered_df["MonthYear"] = filtered_df["Order Date"].dt.strftime("%b %Y")
                peak_month   = filtered_df.groupby("MonthYear")["Sales"].sum().idxmax()
                loss_pct     = len(filtered_df[filtered_df["Profit"]<0]) / len(filtered_df) * 100

                ic1,ic2,ic3,ic4 = st.columns(4)
                cards = [
                    (ic1, "#22C55E", "#86EFAC", "#D1FAE5", "Top Category",  f"{best_cat} leads with ${best_cat_val:,.0f} in sales"),
                    (ic2, "#3B82F6", "#93C5FD", "#DBEAFE", "Best Region",   f"{best_region} shows strongest performance"),
                    (ic3, "#F59E0B", "#FCD34D", "#FEF3C7", "Peak Month",    f"{peak_month} has highest sales volume"),
                    (ic4, "#EF4444", "#FCA5A5", "#FEE2E2", "Margin Alert",  f"{loss_pct:.1f}% transactions at a loss"),
                ]
                for col_w, border, label_col, text_col, title, text in cards:
                    with col_w:
                        st.markdown(f"""
                        <div class="insight-card" style="border-top-color:{border};">
                            <div style="font-size:10px;font-weight:700;color:{label_col};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">{title}</div>
                            <div style="font-size:14px;color:{text_col};font-weight:600;line-height:1.4;">{text}</div>
                        </div>""", unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Insights unavailable: {e}")

        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

        # ── Charts ─────────────────────────────────────────────────────────
        if can(PERM_VIEW_ALL_CHARTS):
            st.markdown('<div class="section-title">Sales and Profit Analysis</div>', unsafe_allow_html=True)

            col_l, col_r = st.columns(2, gap="medium")
            with col_l:
                st.markdown('<div class="chart-card"><div class="chart-label">Sales by Category</div>', unsafe_allow_html=True)
                try:
                    cat_data = filtered_df.groupby("Category")["Sales"].sum().reset_index()
                    fig = px.pie(cat_data, values="Sales", names="Category", hole=0.5,
                                 color_discrete_sequence=["#C084FC","#38BDF8","#86EFAC"])
                    fig.update_traces(textposition='inside', textinfo='percent+label', textfont=dict(size=11,color="white"))
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=260,
                                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                      font=dict(color="#E0E0E0",size=11), legend=dict(font=dict(color="#E0E0E0",size=10)))
                    st.plotly_chart(fig, use_container_width=True, key="donut_cat")
                except Exception as e:
                    st.warning(f"Chart unavailable: {e}")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="chart-card"><div class="chart-label">Top 5 Products by Sales</div>', unsafe_allow_html=True)
                try:
                    top = filtered_df.groupby("Product Name")["Sales"].sum().nlargest(5).reset_index()
                    fig = px.bar(top, x="Sales", y="Product Name", orientation="h",
                                 color="Sales", color_continuous_scale=["#5B21B6","#C084FC"])
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=260,
                                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                      font=dict(color="#E0E0E0",size=10),
                                      xaxis=dict(showgrid=False), yaxis=dict(tickfont=dict(color="#E0E0E0",size=9)))
                    st.plotly_chart(fig, use_container_width=True, key="top_prod")
                except Exception as e:
                    st.warning(f"Chart unavailable: {e}")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_r:
                st.markdown('<div class="chart-card"><div class="chart-label">Monthly Sales Trend</div>', unsafe_allow_html=True)
                try:
                    monthly = filtered_df.groupby("MonthStr")["Sales"].sum().reset_index()
                    fig = px.line(monthly, x="MonthStr", y="Sales", markers=True, line_shape="spline")
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=260,
                                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                      font=dict(color="#E0E0E0",size=10),
                                      xaxis=dict(showgrid=False,tickfont=dict(color="#9CA3AF",size=8)),
                                      yaxis=dict(showgrid=False,tickfont=dict(color="#9CA3AF",size=9)))
                    fig.update_traces(line=dict(color="#C084FC",width=2.5), marker=dict(size=5,color="#00D4FF"))
                    st.plotly_chart(fig, use_container_width=True, key="monthly_trend")
                except Exception as e:
                    st.warning(f"Chart unavailable: {e}")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="chart-card"><div class="chart-label">Profit vs Sales</div>', unsafe_allow_html=True)
                try:
                    fig = px.scatter(filtered_df, x="Sales", y="Profit", color="Category", opacity=0.65,
                                     color_discrete_sequence=["#C084FC","#38BDF8","#86EFAC"])
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=260,
                                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                      font=dict(color="#E0E0E0",size=10),
                                      xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
                                      legend=dict(font=dict(color="#E0E0E0",size=10)))
                    st.plotly_chart(fig, use_container_width=True, key="scatter_ps")
                except Exception as e:
                    st.warning(f"Chart unavailable: {e}")
                st.markdown('</div>', unsafe_allow_html=True)

            # Sales by Region full width
            st.markdown('<div class="chart-card"><div class="chart-label">Sales by Region</div>', unsafe_allow_html=True)
            try:
                reg = filtered_df.groupby("Region")["Sales"].sum().reset_index()
                fig = px.bar(reg, x="Region", y="Sales", color="Region", text_auto=True,
                             color_discrete_sequence=["#86EFAC","#38BDF8","#FCD34D","#F9A8D4"])
                fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=240,
                                  plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#E0E0E0",size=10), showlegend=False)
                fig.update_traces(texttemplate='$%{y:,.0f}', textposition='outside',
                                  textfont=dict(color="#E0E0E0",size=10))
                st.plotly_chart(fig, use_container_width=True, key="reg_sales")
            except Exception as e:
                st.warning(f"Chart unavailable: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

        # ── Top Products table + Smart Recommendations ─────────────────────
        col_tbl, col_rec = st.columns([1.4, 1], gap="medium")
        with col_tbl:
            st.markdown('<div class="section-title">Top Products</div>', unsafe_allow_html=True)
            if can(PERM_VIEW_RAW_DATA):
                with st.expander("View Detailed Data", expanded=False):
                    display_df = filtered_df[[c for c in ['Region','Category','Sub-Category','Product Name','Sales','Profit','Quantity','Discount','Order Date'] if c in filtered_df.columns]].copy()
                    if 'Sales'      in display_df.columns: display_df['Sales']   = display_df['Sales'].apply(lambda x: f"${x:,.0f}")
                    if 'Profit'     in display_df.columns: display_df['Profit']  = display_df['Profit'].apply(lambda x: f"${x:,.0f}")
                    if 'Discount'   in display_df.columns: display_df['Discount']= display_df['Discount'].apply(lambda x: f"{x*100:.0f}%")
                    if 'Order Date' in display_df.columns: display_df['Order Date']= display_df['Order Date'].dt.strftime('%Y-%m-%d')
                    st.dataframe(display_df, use_container_width=True, height=380)

        with col_rec:
            st.markdown('<div class="section-title">Smart Recommendations</div>', unsafe_allow_html=True)
            try:
                analyzer_tmp = RetailDataAnalyzer.__new__(RetailDataAnalyzer)
                active_df_tmp = get_active_df()
                if active_df_tmp is not None:
                    active_df_tmp = active_df_tmp.copy()
                    if "shipping_delay_days" not in active_df_tmp.columns:
                        active_df_tmp["shipping_delay_days"] = 0
                    analyzer_tmp.df = active_df_tmp
                    kpi_vals = analyzer_tmp.calculate_kpis()
                    recs = generate_smart_recommendations(kpi_vals)
                    colors = ["#4ade80","#C084FC","#38BDF8","#FCD34D"]
                    for i, rec in enumerate(recs[:4]):
                        c = colors[i % len(colors)]
                        st.markdown(f'<div class="rec-card"><span style="color:{c};font-weight:700">→ </span>{rec}</div>', unsafe_allow_html=True)
            except Exception:
                st.markdown('<div class="rec-card"><span style="color:#C084FC;font-weight:700">→ </span>Scale top-performing categories to maximise revenue</div>', unsafe_allow_html=True)
                st.markdown('<div class="rec-card"><span style="color:#4ade80;font-weight:700">→ </span>Leverage customer base with loyalty programmes</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# PAGE: VISUALIZATION
# ══════════════════════════════════════════════════════════════════════════
elif page == "Visualization":
    if not dataset_loaded or filtered_df.empty:
        st.info("No data loaded. Go to Data Upload first.")
    else:
        # Auto-refresh controls
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            auto = st.toggle("Auto-Refresh", value=False, key="auto_tog")
        with c2:
            iv = st.selectbox("Interval (s)", [10, 30, 60, 120], index=1, key="iv_sel")
        with c3:
            if st.button("Refresh Now", key="ref_now"):
                st.rerun()

        # Correlation matrix
        st.markdown('<div class="section-title">Correlation Intelligence Matrix</div>', unsafe_allow_html=True)
        num_cols = filtered_df.select_dtypes(include=np.number).columns.tolist()
        if len(num_cols) >= 2:
            try:
                corr = filtered_df[num_cols[:8]].corr()
                fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="Purples", zmin=-1, zmax=1)
                fig.update_layout(margin=dict(l=0,r=0,t=30,b=0), height=320,
                                  plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#E0E0E0",size=10))
                st.plotly_chart(fig, use_container_width=True, key="corr_heat")
            except Exception as e:
                st.warning(f"Correlation chart unavailable: {e}")

        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

        # 3-column charts
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            st.markdown('<div class="section-title">Month-over-Month</div>', unsafe_allow_html=True)
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            try:
                if "Order Date" in filtered_df.columns and "Sales" in filtered_df.columns:
                    tmp = filtered_df.copy()
                    tmp["_m"] = tmp["Order Date"].dt.month
                    mom = tmp.groupby("_m")["Sales"].sum().reset_index()
                    fig = px.bar(mom, x="_m", y="Sales", color_discrete_sequence=["#C084FC"])
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=230,
                                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                      font=dict(color="#E0E0E0",size=10), xaxis=dict(showgrid=False),
                                      yaxis=dict(showgrid=False))
                    st.plotly_chart(fig, use_container_width=True, key="mom_chart")
            except Exception as e:
                st.info(f"{e}")
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="section-title">Sales by Region</div>', unsafe_allow_html=True)
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            try:
                if "Region" in filtered_df.columns and "Sales" in filtered_df.columns:
                    reg = filtered_df.groupby("Region")["Sales"].sum().reset_index()
                    fig = px.pie(reg, names="Region", values="Sales", hole=0.5,
                                 color_discrete_sequence=["#C084FC","#38BDF8","#86EFAC","#FCD34D"])
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=230,
                                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                      font=dict(color="#E0E0E0",size=10), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True, key="region_donut")
            except Exception as e:
                st.info(f"{e}")
            st.markdown('</div>', unsafe_allow_html=True)

        with c3:
            st.markdown('<div class="section-title">Profit Margin by Category</div>', unsafe_allow_html=True)
            if "Category" in filtered_df.columns and "Sales" in filtered_df.columns and "Profit" in filtered_df.columns:
                try:
                    cat_margin = filtered_df.groupby("Category").apply(
                        lambda x: round(x["Profit"].sum() / x["Sales"].sum() * 100, 1) if x["Sales"].sum() else 0
                    ).reset_index(name="Margin")
                    colors_m = ["#4ade80","#38BDF8","#C084FC","#FCD34D"]
                    for i, row in cat_margin.iterrows():
                        c = colors_m[i % len(colors_m)]
                        pct = max(0, min(float(row["Margin"]), 100))
                        st.markdown(f"""
                        <div style="margin-bottom:10px">
                          <div style="display:flex;justify-content:space-between;font-size:10px;color:rgba(255,255,255,0.55);margin-bottom:3px">
                            <span>{row['Category']}</span><span style="color:{c};font-weight:600">{pct}%</span>
                          </div>
                          <div class="prog-track"><div class="prog-fill" style="width:{pct}%;background:{c}"></div></div>
                        </div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.info(f"{e}")

        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

        # Scatter + Activity feed
        c4, c5 = st.columns([1.3, 1], gap="medium")
        with c4:
            st.markdown('<div class="section-title">Profit vs Sales Scatter</div>', unsafe_allow_html=True)
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            try:
                fig = px.scatter(filtered_df, x="Sales", y="Profit", color="Category", opacity=0.65,
                                 color_discrete_sequence=["#C084FC","#38BDF8","#86EFAC"])
                fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=250,
                                  plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#E0E0E0",size=10),
                                  xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
                                  legend=dict(font=dict(color="#E0E0E0",size=10)))
                st.plotly_chart(fig, use_container_width=True, key="scatter_viz")
            except Exception as e:
                st.info(f"{e}")
            st.markdown('</div>', unsafe_allow_html=True)

        with c5:
            st.markdown('<div class="section-title">Activity Feed</div>', unsafe_allow_html=True)
            activities = [
                ("Revenue spike detected in top region",       "2 min ago"),
                (f"{user['full_name']} is viewing dashboard",  "Just now"),
                ("PDF report available for download",          "1 hr ago"),
                ("Data quality check completed",               "Yesterday"),
            ]
            for msg, tm in activities:
                st.markdown(f"""
                <div class="act-item">
                  <div>
                    <div style="font-size:11px;color:rgba(255,255,255,0.75)">{msg}</div>
                    <div style="font-size:9px;color:rgba(255,255,255,0.28);margin-top:1px">{tm}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

        if auto:
            time.sleep(iv); st.rerun()

# ══════════════════════════════════════════════════════════════════════════
# PAGE: PREDICTIVE ANALYTICS
# ══════════════════════════════════════════════════════════════════════════
elif page == "Predictive Analytics":
    st.markdown('<div class="section-title">Predictive Analytics</div>', unsafe_allow_html=True)
    active_df = get_active_df()

    if active_df is None or active_df.empty:
        st.info("No data loaded. Go to Data Upload first.")
    else:
        # KPI row
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            st.markdown('<div class="kpi-card"><div class="kpi-top-bar" style="background:linear-gradient(90deg,#C084FC,#818CF8)"></div><div class="kpi-body"><div class="kpi-label">Model</div><div class="kpi-value" style="font-size:1.2rem;color:#C084FC">Predictive Engine</div></div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="kpi-card"><div class="kpi-top-bar" style="background:linear-gradient(90deg,#38BDF8,#0EA5E9)"></div><div class="kpi-body"><div class="kpi-label">Forecast Horizon</div><div class="kpi-value" style="font-size:1.2rem;color:#38BDF8">6 Months</div></div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="kpi-card"><div class="kpi-top-bar" style="background:linear-gradient(90deg,#86EFAC,#22C55E)"></div><div class="kpi-body"><div class="kpi-label">Target Growth</div><div class="kpi-value" style="font-size:1.2rem;color:#86EFAC">10%</div></div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Run Forecast", type="primary", key="run_fc"):
            with st.spinner("Running predictive engine…"):
                try:
                    engine = SalesPredictiveEngine(df=active_df.copy())
                    engine.run_full_forecast(forecast_periods=6, target_growth_pct=10.0)
                    st.success("Forecast complete.")
                except Exception as e:
                    st.error(f"Predictive engine error: {e}")

        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

        # Insights + Recommendations
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            st.markdown('<div class="section-title">AI Insights</div>', unsafe_allow_html=True)
            try:
                analyzer_tmp = RetailDataAnalyzer.__new__(RetailDataAnalyzer)
                tmp = active_df.copy()
                if "shipping_delay_days" not in tmp.columns:
                    tmp["shipping_delay_days"] = 0
                analyzer_tmp.df = tmp
                kpi_vals = analyzer_tmp.calculate_kpis()
                for ins in generate_ai_insights(kpi_vals):
                    st.info(ins)
            except Exception as e:
                st.warning(f"Insights unavailable: {e}")

        with col2:
            st.markdown('<div class="section-title">Smart Recommendations</div>', unsafe_allow_html=True)
            try:
                for rec in generate_smart_recommendations(kpi_vals):
                    st.success(rec)
            except Exception:
                st.info("Run forecast first to generate recommendations.")

# ══════════════════════════════════════════════════════════════════════════
# PAGE: DATA UPLOAD (Team 1)
# ══════════════════════════════════════════════════════════════════════════
elif page == "Data Upload":
    uploaded = file_upload_section()
    if uploaded is not None:
        st.session_state["uploaded_df"] = uploaded
        load_data.clear()
        st.success("Dataset ready. Navigate to Dashboard to view analytics.")

# ══════════════════════════════════════════════════════════════════════════
# PAGE: DATASET PROFILING (Team 1)
# ══════════════════════════════════════════════════════════════════════════
elif page == "Dataset Profiling":
    if st.session_state.get("uploaded_df") is None:
        st.warning("Please upload a dataset first using Data Upload.")
    else:
        dataset_profiling_section(st.session_state["uploaded_df"])

# ══════════════════════════════════════════════════════════════════════════
# PAGE: DATA QUALITY (Team 1)
# ══════════════════════════════════════════════════════════════════════════
elif page == "Data Quality":
    if st.session_state.get("uploaded_df") is None:
        st.warning("Please upload a dataset first using Data Upload.")
    else:
        data_quality_section(st.session_state["uploaded_df"])

# ══════════════════════════════════════════════════════════════════════════
# PAGE: MEET OUR TEAM
# ══════════════════════════════════════════════════════════════════════════
elif page == "Meet Our Team":
    TEAM = [
        ("Naheen Kauser",           "Team Lead",        "Module 4", "#a78bfa", "naheenkauser113@gmail.com",        "https://in.linkedin.com/in/naheen-kauser-02957a323",                     "https://github.com/NaheenKauserr",         True),
        ("Manu Naik",               "Systems Engineer", "Module 5", "#60a5fa", "manupnaik639@gmail.com",           "https://www.linkedin.com/in/manu-naik-73bb702a7",                        "https://github.com/manunaik111",           False),
        ("Dhaval Shah",             "NLP Engineer",     "Module 2", "#818cf8", "d34058397@gmail.com",              "https://www.linkedin.com/in/dhaval-shah1628",                            "https://github.com/Dhaval-max3",           False),
        ("Mohammed Ammar",          "Data Engineer",    "Module 1", "#38bdf8", "mohammedammar060802@gmail.com",    "https://www.linkedin.com/in/mohammed-ammar-bin-zameer-589220363/",       "https://github.com/ammar3633",             False),
        ("Yusuf Chonche",           "UI/Dashboard Dev", "Module 4", "#34d399", "yusufchonche0@gmail.com",          "https://www.linkedin.com/in/yusuf-chonche-5114892ba/",                   "https://github.com/yusufchonche0-web",     False),
        ("Vaishnavi Metri",         "Analytics Eng",    "Module 3", "#fbbf24", "vaishnavimetri234@gmail.com",      "https://www.linkedin.com/in/vaishnavi-metri-578b0835a",                  "https://github.com/vaishnavimetri234-v11s",False),
        ("Anoosha Kembhavi",        "Systems Engineer", "Module 5", "#f9a8d4", "anooshakembhavi@gmail.com",        "http://www.linkedin.com/in/anoosha-kembhavi",                            "https://github.com/anooshakembhavi-afk",   False),
        ("Snehal Kamble",           "Data Engineer",    "Module 1", "#fb923c", "kamblesnehal578@gmail.com",        "https://www.linkedin.com/in/snehal-k-b48369318",                         "https://github.com/kamblesnehal578-sketch",False),
        ("Nazhat Naikwadi",         "Data Engineer",    "Module 1", "#f472b6", "nazhatnaikwadi@gmail.com",         "https://linkedin.com/in/nazhatnaikwadi",                                 "https://github.com/nazhatnaikwadi",        False),
        ("Keerti Gadigeppagoudar",  "Analytics Eng",    "Module 3", "#2dd4bf", "keerti.s.g2020@gmail.com",         "https://www.linkedin.com/in/keertig",                                    "https://github.com/keertiG-1296",          False),
        ("Samruddhi Patil",         "NLP Engineer",     "Module 2", "#4ade80", "patilsamruddhi863@gmail.com",      "https://www.linkedin.com/in/samruddhi-patil-a1575933a",                  "https://github.com/samruddhi128",          False),
    ]

    st.markdown("""
    <div style="text-align:center;padding:28px 32px 22px;background:rgba(18,18,35,0.75);border:1px solid rgba(123,47,190,0.25);border-radius:20px;margin-bottom:22px;">
      <div style="font-size:26px;font-weight:800;color:#E0E0E0;letter-spacing:.04em;text-transform:uppercase;margin-bottom:6px;">Meet Our Team</div>
      <div style="font-size:13px;color:#6B7280;">11 interns · 5 modules · 1 AI platform · Genesis Training</div>
    </div>""", unsafe_allow_html=True)

    cols1 = st.columns(5, gap="small")
    for i, (name, role, module, color, email, li, gh, is_lead) in enumerate(TEAM[:5]):
        with cols1[i]:
            initials = "".join(w[0].upper() for w in name.split())[:2]
            lead_badge = '<div style="text-align:center;margin-bottom:6px;"><span style="background:#F59E0B;color:#fff;font-size:7px;font-weight:700;padding:2px 9px;border-radius:20px;">TEAM LEAD</span></div>' if is_lead else ""
            st.markdown(f"""
            <div style="background:rgba(18,18,35,0.85);border:1.5px solid {color}66;border-radius:18px;padding:18px 10px 14px;text-align:center;min-height:200px;position:relative;">
              {lead_badge}
              <div style="width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,{color}CC,{color}66);display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:800;color:white;margin:0 auto 10px;border:2px solid {color};">
                {initials}</div>
              <div style="font-size:12px;font-weight:700;color:#E0E0E0;margin-bottom:3px">{name}</div>
              <div style="font-size:8px;font-weight:600;color:{color};background:{color}22;border:1px solid {color}44;border-radius:20px;padding:2px 8px;display:inline-block;margin-bottom:8px">{role}</div>
              <div style="font-size:8px;color:#6B7280;margin-bottom:8px">{module}</div>
              <div style="display:flex;justify-content:center;gap:6px;">
                <a href="{li}" target="_blank" style="display:flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:6px;background:rgba(0,119,181,0.2);border:1px solid rgba(0,119,181,0.4);color:#38bdf8;font-size:9px;font-weight:800;text-decoration:none;">in</a>
                <a href="{gh}" target="_blank" style="display:flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:6px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.2);color:#ccc;font-size:9px;text-decoration:none;">gh</a>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    cols2 = st.columns(6, gap="small")
    for i, (name, role, module, color, email, li, gh, is_lead) in enumerate(TEAM[5:]):
        with cols2[i]:
            initials = "".join(w[0].upper() for w in name.split())[:2]
            st.markdown(f"""
            <div style="background:rgba(18,18,35,0.85);border:1.5px solid {color}55;border-radius:16px;padding:14px 8px 12px;text-align:center;min-height:185px;">
              <div style="width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,{color}CC,{color}66);display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:800;color:white;margin:0 auto 8px;border:2px solid {color};">
                {initials}</div>
              <div style="font-size:11px;font-weight:700;color:#E0E0E0;margin-bottom:3px">{name}</div>
              <div style="font-size:7.5px;font-weight:600;color:{color};background:{color}22;border-radius:20px;padding:2px 7px;display:inline-block;margin-bottom:6px">{role}</div>
              <div style="font-size:7.5px;color:#6B7280;margin-bottom:7px">{module}</div>
              <div style="display:flex;justify-content:center;gap:5px;">
                <a href="{li}" target="_blank" style="display:flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:5px;background:rgba(0,119,181,0.2);border:1px solid rgba(0,119,181,0.4);color:#38bdf8;font-size:8px;font-weight:800;text-decoration:none;">in</a>
                <a href="{gh}" target="_blank" style="display:flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:5px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.2);color:#ccc;font-size:8px;text-decoration:none;">gh</a>
              </div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ══════════════════════════════════════════════════════════════════════════
elif page == "Settings":
    st.markdown('<div class="section-title">Settings</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown('<div class="chart-card"><div class="chart-label">Account</div>', unsafe_allow_html=True)
        uname = user['full_name']
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:10px;margin-bottom:10px">
          <div style="font-size:12px;font-weight:500;color:#E0E0E0">{uname}</div>
          <div style="font-size:10px;color:#4ade80;margin-top:3px">Session active</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Sign Out", key="s_logout", use_container_width=True):
            logout_user(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="chart-card"><div class="chart-label">User Management</div>', unsafe_allow_html=True)
        if can(PERM_MANAGE_USERS):
            show_user_management()
        else:
            st.info("Admin access required.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="chart-card"><div class="chart-label">Data</div>', unsafe_allow_html=True)
        if st.button("Clear Uploaded Dataset", use_container_width=True, key="clear_data"):
            st.session_state["uploaded_df"] = None
            load_data.clear()
            st.success("Cleared!")
            st.rerun()
        if st.button("Clear Chat History", use_container_width=True, key="clear_chat"):
            st.session_state.chat_messages = []
            clear_memory()
            st.success("Chat cleared!")
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# USER MANAGEMENT MODAL
# ══════════════════════════════════════════════════════════════════════════
if st.session_state.get('show_user_mgmt') and can(PERM_MANAGE_USERS):
    st.markdown('<div class="fade-long-line"></div>', unsafe_allow_html=True)
    show_user_management()

# ══════════════════════════════════════════════════════════════════════════
# FLOATING CHATBOT (always visible)
# ══════════════════════════════════════════════════════════════════════════
if can(PERM_USE_CHATBOT):
    # Toggle button
    btn_container = st.container()
    with btn_container:
        btn_label = "Close Assistant" if st.session_state.chat_open else "AI Assistant"
        if st.button(btn_label, key="float_toggle", type="primary"):
            st.session_state.chat_open = not st.session_state.chat_open
            st.rerun()
    btn_container.float("bottom: 60px; right: 24px; width: auto;")

    # Chat panel
    if st.session_state.chat_open:
        chat_container = st.container()
        with chat_container:
            st.markdown('<div class="chat-header">AI Sales Assistant</div>', unsafe_allow_html=True)

            # Voice input button
            col_voice, col_clear = st.columns([1, 1])
            with col_voice:
                if st.button("🎤 Voice Input", key="voice_btn"):
                    with st.spinner("Listening…"):
                        try:
                            text = transcribe_voice()
                            if text:
                                st.session_state.pending_q = text
                                st.rerun()
                            else:
                                st.warning("Could not transcribe. Try again.")
                        except Exception as e:
                            st.warning(f"Voice error: {e}")
            with col_clear:
                if st.button("Clear", key="clear_btn", type="secondary"):
                    clear_memory()
                    st.session_state.chat_messages = []
                    st.rerun()

            # Messages
            if not st.session_state.chat_messages:
                st.markdown('<div class="msg-bot">Hello. I am your AI Sales Assistant.<br>Ask me anything about the sales data.</div>', unsafe_allow_html=True)
            else:
                for msg in st.session_state.chat_messages[-10:]:
                    css     = "msg-user" if msg['role'] == 'user' else "msg-bot"
                    content = msg['content'].replace('<','&lt;').replace('>','&gt;')
                    st.markdown(f'<div class="{css}">{content}</div>', unsafe_allow_html=True)

                    # Voice output for last bot message
                    if msg['role'] == 'assistant' and msg == st.session_state.chat_messages[-1]:
                        try:
                            audio_bytes = speak(msg['content'])
                            st.audio(audio_bytes, format="audio/mp3")
                        except Exception:
                            pass

            # Quick questions
            st.markdown("**Quick Questions:**")
            q1, q2 = st.columns(2)
            with q1:
                if st.button("Top Region",   key="qq1"): st.session_state.pending_q = "Which region has the highest sales?"; st.rerun()
                if st.button("Category",     key="qq2"): st.session_state.pending_q = "Which category has highest profit?";  st.rerun()
            with q2:
                if st.button("Top Products", key="qq3"): st.session_state.pending_q = "What are the top 5 products?";        st.rerun()
                if st.button("Monthly Trend",key="qq4"): st.session_state.pending_q = "Show me the monthly sales trend";     st.rerun()

            user_input = st.chat_input("Ask about sales data...")
            if user_input:
                st.session_state.pending_q = user_input
                st.rerun()

        chat_container.float(
            "bottom: 120px; right: 24px; width: 360px; "
            "background: rgba(10,10,22,0.92); border-radius: 18px; "
            "box-shadow: 0 0 40px rgba(123,47,190,0.3); "
            "border: 1px solid rgba(123,47,190,0.3); "
            "padding: 0 14px 14px 14px; "
            "max-height: 520px; overflow-y: auto; z-index: 999; "
            "backdrop-filter: blur(20px);"
        )