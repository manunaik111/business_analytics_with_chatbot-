# main_app.py
# Team 5 — Integration & Interface
# Premium Midnight Aurora + New Dashboard + All 8 Premium Features

import streamlit as st
from streamlit_float import *
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import time

sys.path.append(os.path.dirname(__file__))

from chatbot.chatbot_engine import chat, clear_memory, initialize_memory, get_analyzer
from report_generator import generate_excel_report, generate_pdf_report

# ── Page Configuration ────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "AI Sales Analytics Dashboard"
    }
)

float_init()
initialize_memory()

if 'chat_open'   not in st.session_state: st.session_state.chat_open   = False
if 'pending_q'   not in st.session_state: st.session_state.pending_q   = None
if 'app_loaded'  not in st.session_state: st.session_state.app_loaded  = False
if 'api_error'   not in st.session_state: st.session_state.api_error   = None

# ── Premium Midnight Aurora CSS ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

#MainMenu {visibility: hidden;}
footer    {visibility: hidden;}

* { font-family: 'Inter', sans-serif !important; }

/* ── 1. Base dark background with subtle radial glow ── */
.stApp {
    background-color: #080B14 !important;
    background-image:
        radial-gradient(ellipse at 15% 15%, rgba(123,47,190,0.07) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 85%, rgba(0,212,255,0.04) 0%, transparent 55%);
}
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 100% !important;
}
h1,h2,h3,p,span,div,label { color: #E0E0E0 !important; }

/* ── 2. Animated gradient title ── */
@keyframes gradientShift {
    0%   { background-position: 0% 50%;   }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%;   }
}
.animated-title {
    background: linear-gradient(270deg, #00D4FF, #C084FC, #818CF8, #38BDF8, #00D4FF);
    background-size: 400% 400%;
    animation: gradientShift 6s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.6rem;
    font-weight: 900;
    letter-spacing: -1.5px;
    text-align: center;
    margin: 0;
    line-height: 1.15;
}
.title-sub {
    color: #4B5563 !important;
    font-size: 12px;
    text-align: center;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 8px;
    font-weight: 500;
}

/* ── 3. Glowing gradient divider ── */
.glow-divider {
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%,
        rgba(123,47,190,0.9) 25%,
        rgba(0,212,255,0.9) 50%,
        rgba(123,47,190,0.9) 75%,
        transparent 100%);
    margin: 1.6rem 0;
    border: none;
    box-shadow: 0 0 10px rgba(123,47,190,0.35), 0 0 20px rgba(0,212,255,0.15);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A0A1A 0%, #0F0F22 100%) !important;
    border-right: 1px solid rgba(123,47,190,0.25) !important;
}
[data-testid="stSidebar"] * { color: #E0E0E0 !important; }
[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #1A1A30 !important;
    color: white !important;
    border: 1px solid rgba(123,47,190,0.4) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] * { color: white !important; }
div[data-baseweb="popover"] div[data-baseweb="menu"] {
    background-color: #1A1A30 !important;
}
div[data-baseweb="popover"] div[data-baseweb="menu"] li {
    color: white !important;
    background-color: #1A1A30 !important;
}
div[data-baseweb="popover"] div[data-baseweb="menu"] li:hover {
    background-color: #2A2A45 !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #7B2FBE, #5B21B6) !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    width: 100% !important;
    font-weight: 700 !important;
    box-shadow: 0 0 15px rgba(123,47,190,0.35) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    box-shadow: 0 0 25px rgba(123,47,190,0.55) !important;
    transform: translateY(-1px) !important;
}

/* ── 4. KPI Cards — Glassmorphism with gradient top bar ── */
.kpi-card {
    background: rgba(18, 18, 35, 0.75);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-radius: 18px;
    border: 1px solid rgba(123,47,190,0.22);
    box-shadow:
        0 8px 32px rgba(0,0,0,0.45),
        inset 0 1px 0 rgba(255,255,255,0.04);
    overflow: hidden;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    margin-bottom: 0.5rem;
}
.kpi-card:hover {
    transform: translateY(-5px);
    box-shadow:
        0 20px 48px rgba(0,0,0,0.55),
        0 0 24px rgba(123,47,190,0.35),
        inset 0 1px 0 rgba(255,255,255,0.07);
    border-color: rgba(123,47,190,0.55);
}
.kpi-top-bar {
    height: 3px;
    width: 100%;
}
.kpi-body {
    padding: 10px 10px 12px 10px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
}
.kpi-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    margin-bottom: 2px;
}
.kpi-label {
    font-size: 9px !important;
    color: #6B7280 !important;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 700;
}
.kpi-icon { font-size: 14px; }
.kpi-value {
    font-size: 1.6rem !important;
    font-weight: 900 !important;
    line-height: 1.1;
    margin-bottom: 0;
}

/* ── 5. Section titles ── */
.section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 10px !important;
    font-weight: 700 !important;
    color: #4B5563 !important;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    margin: 28px 0 14px 0;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(123,47,190,0.6), transparent);
}

/* ── 6. Glassmorphism chart cards ── */
.chart-card {
    background: rgba(12, 12, 28, 0.8);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-radius: 18px;
    padding: 16px;
    border: 1px solid rgba(123,47,190,0.18);
    box-shadow:
        0 8px 32px rgba(0,0,0,0.4),
        inset 0 1px 0 rgba(255,255,255,0.02);
    margin-bottom: 14px;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.chart-card:hover {
    border-color: rgba(123,47,190,0.38);
    box-shadow:
        0 14px 44px rgba(0,0,0,0.5),
        0 0 18px rgba(123,47,190,0.12);
}
.chart-label {
    font-size: 10px;
    font-weight: 700;
    color: #6B7280 !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(123,47,190,0.15);
}

/* ── 7. Insight cards ── */
.insight-card {
    background: rgba(12,12,28,0.8);
    backdrop-filter: blur(20px);
    border-radius: 14px;
    padding: 16px;
    border-top: 3px solid transparent;
    box-shadow: 0 8px 28px rgba(0,0,0,0.35);
    transition: transform 0.2s ease;
    height: 100%;
}
.insight-card:hover { transform: translateY(-3px); }

/* ── 8. Download buttons ── */
.stDownloadButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 9px 18px !important;
    border: 1px solid rgba(123,47,190,0.45) !important;
    background: rgba(123,47,190,0.15) !important;
    color: #C084FC !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    background: rgba(123,47,190,0.35) !important;
    border-color: rgba(123,47,190,0.75) !important;
    box-shadow: 0 0 18px rgba(123,47,190,0.35) !important;
    transform: translateY(-1px) !important;
}

/* ── Primary / Secondary buttons ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#7B2FBE,#5B21B6) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    box-shadow: 0 0 14px rgba(123,47,190,0.32) !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 26px rgba(123,47,190,0.52) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(18,18,35,0.7) !important;
    color: #C084FC !important;
    border: 1px solid rgba(123,47,190,0.38) !important;
    border-radius: 10px !important; font-weight: 500 !important;
    backdrop-filter: blur(10px) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(123,47,190,0.18) !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: rgba(12,12,28,0.8) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(123,47,190,0.22) !important;
    border-radius: 14px !important;
}

/* ── Chat ── */
.msg-user {
    background: linear-gradient(135deg,rgba(123,47,190,0.85),rgba(91,33,182,0.85));
    backdrop-filter: blur(10px);
    color: white; padding: 10px 15px;
    border-radius: 16px 16px 3px 16px; margin: 6px 0;
    font-size: 13px; word-wrap: break-word; text-align: right;
    line-height: 1.5; border: 1px solid rgba(123,47,190,0.4);
}
.msg-bot {
    background: rgba(18,18,35,0.85); backdrop-filter: blur(10px);
    color: #E0E0E0; padding: 10px 15px;
    border-radius: 16px 16px 16px 3px; margin: 6px 0;
    font-size: 13px; word-wrap: break-word; text-align: left;
    border: 1px solid rgba(123,47,190,0.2); line-height: 1.5;
}
.chat-header {
    background: linear-gradient(135deg,#7B2FBE,#5B21B6);
    color: white; padding: 14px 18px;
    border-radius: 14px 14px 0 0; font-weight: 700;
    font-size: 15px; margin-bottom: 10px;
    box-shadow: 0 4px 16px rgba(123,47,190,0.3);
}
div[data-testid="stChatInput"] > div {
    border-radius: 12px !important;
    border: 1px solid rgba(123,47,190,0.38) !important;
    background: rgba(18,18,35,0.85) !important;
    backdrop-filter: blur(10px) !important;
}
div[data-testid="stChatInput"] > div:focus-within {
    border-color: #7B2FBE !important;
    box-shadow: 0 0 0 3px rgba(123,47,190,0.18) !important;
}

/* ── Alert ── */
div[data-testid="stAlert"] {
    background: rgba(18,18,35,0.75) !important;
    border: 1px solid rgba(123,47,190,0.28) !important;
    border-radius: 12px !important; backdrop-filter: blur(10px) !important;
}

/* ── Quick analysis box ── */
.quick-box {
    background: rgba(18,18,35,0.75);
    backdrop-filter: blur(16px);
    border-radius: 14px;
    padding: 14px 16px;
    border: 1px solid rgba(123,47,190,0.2);
    margin-top: 8px;
}
.quick-row {
    padding: 7px 0;
    border-bottom: 1px solid rgba(123,47,190,0.1);
    font-size: 13px;
    color: #D1D5DB !important;
}
.quick-row:last-child { border-bottom: none; }
.quick-label {
    font-size: 10px;
    font-weight: 700;
    color: #6B7280 !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

[data-testid="stHorizontalBlock"] { gap: 8px !important; }
[data-testid="column"] { min-width: 80px !important; }
</style>
""", unsafe_allow_html=True)

# ── Startup Loading Screen ────────────────────────────────────────────
if not st.session_state.app_loaded:
    with st.spinner(""):
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;padding:130px 20px;text-align:center;">
            <div style="font-size:38px;font-weight:900;margin-bottom:10px;
                background:linear-gradient(270deg,#00D4FF,#C084FC,#818CF8,#00D4FF);
                background-size:400% 400%;
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                AI Sales Analytics
            </div>
            <div style="font-size:11px;color:#4B5563;margin-bottom:44px;
                        letter-spacing:3px;text-transform:uppercase;font-weight:600;">
                Initialising Dashboard
            </div>
            <div style="font-size:13px;color:#7B2FBE;margin:5px 0;font-weight:500;">
                Loading sales dataset...
            </div>
            <div style="font-size:13px;color:#7B2FBE;margin:5px 0;font-weight:500;">
                Initialising AI assistant...
            </div>
            <div style="font-size:13px;color:#7B2FBE;margin:5px 0;font-weight:500;">
                Building analytics engine...
            </div>
        </div>
        """, unsafe_allow_html=True)
        try:
            analyzer = get_analyzer()
            time.sleep(1.2)
            st.session_state.app_loaded = True
            st.session_state.api_error  = None
            st.rerun()
        except Exception as e:
            st.session_state.app_loaded = True
            st.session_state.api_error  = str(e)
            st.rerun()

# ── Process pending question ──────────────────────────────────────────
if st.session_state.pending_q:
    question = st.session_state.pending_q
    st.session_state.pending_q = None
    st.session_state.chat_messages.append({'role': 'user', 'content': question})
    with st.spinner(""):
        response = chat(question)
    if response:
        if response.startswith("Sorry, I encountered an error:"):
            err = response
            if "429" in err or "quota" in err.lower():
                friendly = "The AI assistant has hit its usage limit. Please wait a few minutes and try again."
            elif "401" in err or "authentication" in err.lower():
                friendly = "API key issue. Please check your secrets.toml configuration."
            else:
                friendly = "Something went wrong. Please try again in a moment."
            st.session_state.chat_messages.append({'role': 'assistant', 'content': friendly})
        else:
            st.session_state.chat_messages.append({'role': 'assistant', 'content': response})
    st.rerun()

# ── Load and prepare dataset ──────────────────────────────────────────
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
    df = df.dropna(subset=["Sales","Profit","Category","Region"])
    return df

try:
    df = load_data()
    dataset_loaded = True
except Exception as e:
    dataset_loaded = False
    df = pd.DataFrame()
    st.error(f"Could not load dataset: {str(e)}")

# ── Filter function ───────────────────────────────────────────────────
def apply_filters(df, cat, region, year, profit):
    filtered = df.copy()
    if cat    != "All": filtered = filtered[filtered["Category"] == cat]
    if region != "All": filtered = filtered[filtered["Region"]   == region]
    if year   != "All": filtered = filtered[filtered["Year"]     == int(year)]
    if profit == "Profitable":  filtered = filtered[filtered["Profit"] > 0]
    elif profit == "Loss Making": filtered = filtered[filtered["Profit"] < 0]
    return filtered

# ── KPI computation ───────────────────────────────────────────────────
def compute_kpis(df):
    if df.empty: return {}
    total_sales = df["Sales"].sum()
    return {
        "total_sales":   total_sales,
        "avg_order":     df["Sales"].mean(),
        "total_profit":  df["Profit"].sum(),
        "profit_margin": (df["Profit"]/df["Sales"]).mean()*100 if total_sales else 0,
        "profit_ratio":  (df["Profit"].sum()/total_sales)*100  if total_sales else 0,
        "avg_discount":  df["Discount"].mean()*100,
        "avg_shipping":  df["shipping_delay_days"].mean() if "shipping_delay_days" in df.columns else 0,
        "total_records": len(df),
    }

def fmt(v, pre='', suf='', dec=0):
    if isinstance(v,(int,float)):
        return f"{pre}{v:,.{dec}f}{suf}"
    return str(v)

# ── Mini trend sparkline ──────────────────────────────────────────────
def mini_line(df, metric="Sales"):
    if df.empty or metric not in df.columns:
        return go.Figure()
    monthly = df.groupby(df["Order Date"].dt.to_period("M"))[metric].sum().reset_index()
    monthly["Date"] = monthly["Order Date"].dt.start_time
    fig = px.line(monthly, x="Date", y=metric, line_shape="spline")
    fig.update_layout(
        width=200, height=32,
        margin=dict(l=0,r=0,t=0,b=0),
        xaxis_visible=False, yaxis_visible=False,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False
    )
    fig.update_traces(line=dict(color="#C084FC", width=1.5))
    return fig

# ── Sidebar ───────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="text-align:center;padding:16px 0 10px 0;">
    <div style="font-size:15px;font-weight:800;
        background:linear-gradient(90deg,#C084FC,#00D4FF);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
        Dashboard Filters
    </div>
    <div style="font-size:10px;color:#4B5563;letter-spacing:2px;
                text-transform:uppercase;margin-top:4px;font-weight:600;">
        Explore the dataset
    </div>
</div>
""", unsafe_allow_html=True)
st.sidebar.divider()

if dataset_loaded:
    years = sorted(df["Year"].dropna().unique().astype(int).tolist())
    for k,v in [("year","All"),("category","All"),("region","All"),("profit_status","All")]:
        if k not in st.session_state: st.session_state[k] = v

    sel_cat    = st.sidebar.selectbox("Category",      ["All"]+sorted(df["Category"].unique()), key="category")
    sel_region = st.sidebar.selectbox("Region",        ["All"]+sorted(df["Region"].unique()),   key="region")
    sel_profit = st.sidebar.selectbox("Profit Status", ["All","Profitable","Loss Making"],       key="profit_status")
    sel_year   = st.sidebar.selectbox("Year",          ["All"]+[str(y) for y in years],         key="year")

    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("Reset All Filters", type="primary"):
        for k in ["category","region","profit_status","year"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

    filtered_df = apply_filters(df, sel_cat, sel_region, sel_year, sel_profit)
else:
    filtered_df = pd.DataFrame()

# Quick analysis in sidebar
if not filtered_df.empty:
    st.sidebar.divider()
    st.sidebar.markdown("""
    <div style="font-size:10px;font-weight:700;color:#4B5563;
                text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;">
        Quick Analysis
    </div>
    """, unsafe_allow_html=True)
    try:
        best_cat    = filtered_df.groupby("Category")["Sales"].sum().idxmax()
        top_region  = filtered_df.groupby("Region")["Sales"].sum().idxmax()
        best_profit = filtered_df.groupby("Category")["Profit"].sum().idxmax()
        filtered_df["MonthYear"] = filtered_df["Order Date"].dt.strftime("%b %Y")
        peak_month  = filtered_df.groupby("MonthYear")["Sales"].sum().idxmax()
        st.sidebar.markdown(f"""
        <div class="quick-box">
            <div class="quick-row">
                <div class="quick-label">Best Category</div>
                <div style="color:#C084FC;font-weight:600;">{best_cat}</div>
            </div>
            <div class="quick-row">
                <div class="quick-label">Top Region</div>
                <div style="color:#38BDF8;font-weight:600;">{top_region}</div>
            </div>
            <div class="quick-row">
                <div class="quick-label">Highest Profit</div>
                <div style="color:#86EFAC;font-weight:600;">{best_profit}</div>
            </div>
            <div class="quick-row">
                <div class="quick-label">Peak Month</div>
                <div style="color:#FCD34D;font-weight:600;">{peak_month}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        pass

st.sidebar.divider()
st.sidebar.caption("Sales Analytics Dashboard  |  Data Analysis Project")

# ── Dashboard Header ──────────────────────────────────────────────────
st.markdown("""
<div style="padding: 24px 0 8px 0;">
    <div class="animated-title">Sales Analytics Dashboard</div>
    <div class="title-sub">Real-time Analytics &nbsp;•&nbsp; AI Assistant &nbsp;•&nbsp; Performance Metrics</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

# ── KPI Section ───────────────────────────────────────────────────────
if dataset_loaded and not filtered_df.empty:
    kpis = compute_kpis(filtered_df)

    st.markdown('<div class="section-title">Key Performance Indicators</div>',
                unsafe_allow_html=True)

    kpi_data = [
        ("💰", "Total Sales",    fmt(kpis.get("total_sales",0),   pre="$"),          "Sales",                 "linear-gradient(90deg,#C084FC,#818CF8)"),
        ("🛒", "Avg Order",      fmt(kpis.get("avg_order",0),     pre="$", dec=2),    "Sales",                 "linear-gradient(90deg,#38BDF8,#0EA5E9)"),
        ("📈", "Total Profit",   fmt(kpis.get("total_profit",0),  pre="$"),           "Profit",                "linear-gradient(90deg,#86EFAC,#22C55E)"),
        ("🎯", "Profit Margin",  fmt(kpis.get("profit_margin",0), suf="%", dec=1),    "Profit",                "linear-gradient(90deg,#FCD34D,#F59E0B)"),
        ("📊", "Profit Ratio",   fmt(kpis.get("profit_ratio",0),  suf="%", dec=1),    "Profit",                "linear-gradient(90deg,#F9A8D4,#EC4899)"),
        ("🏷️","Avg Discount",   fmt(kpis.get("avg_discount",0),  suf="%", dec=1),    "Discount",              "linear-gradient(90deg,#FCA5A5,#EF4444)"),
        ("🚚", "Avg Shipping",   fmt(kpis.get("avg_shipping",0),  suf="d", dec=1),    "shipping_delay_days",   "linear-gradient(90deg,#6EE7B7,#10B981)"),
        ("🧾", "Total Records",  fmt(kpis.get("total_records",0)),                    "Sales",                 "linear-gradient(90deg,#C4B5FD,#7C3AED)"),
    ]

    cols = st.columns(8)
    for i, (icon, label, value, spark_col, grad) in enumerate(kpi_data):
        with cols[i]:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-top-bar" style="background:{grad};"></div>
                <div class="kpi-body">
                    <div class="kpi-header-row">
                        <span class="kpi-label">{label}</span>
                        <span class="kpi-icon">{icon}</span>
                    </div>
                    <div class="kpi-value" style="background:{grad};
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        background-clip:text;">{value}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if spark_col in filtered_df.columns:
                fig = mini_line(filtered_df, spark_col)
                st.plotly_chart(fig, use_container_width=True,
                                config={'displayModeBar': False},
                                key=f"spark_{i}")

st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

# ── Charts Section ────────────────────────────────────────────────────
if dataset_loaded and not filtered_df.empty:
    st.markdown('<div class="section-title">Sales and Profit Analysis</div>',
                unsafe_allow_html=True)

    col_l, col_r = st.columns(2, gap="medium")

    with col_l:
        # Sales by Category donut
        st.markdown('<div class="chart-card"><div class="chart-label">Sales by Category</div>',
                    unsafe_allow_html=True)
        try:
            cat_data = filtered_df.groupby("Category")["Sales"].sum().reset_index()
            fig = px.pie(cat_data, values="Sales", names="Category", hole=0.5,
                         color_discrete_sequence=["#C084FC","#38BDF8","#86EFAC"])
            fig.update_traces(textposition='inside', textinfo='percent+label',
                              textfont=dict(size=11, color="white"))
            fig.update_layout(
                margin=dict(l=0,r=0,t=0,b=0), height=260,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E0E0E0",size=11),
                legend=dict(font=dict(color="#E0E0E0",size=10))
            )
            st.plotly_chart(fig, use_container_width=True, key="donut_cat")
        except Exception as e:
            st.warning(f"Chart unavailable: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        # Top 5 Products
        st.markdown('<div class="chart-card"><div class="chart-label">Top 5 Products by Sales</div>',
                    unsafe_allow_html=True)
        try:
            top = filtered_df.groupby("Product Name")["Sales"].sum().nlargest(5).reset_index()
            fig = px.bar(top, x="Sales", y="Product Name", orientation="h",
                         color="Sales", color_continuous_scale=["#5B21B6","#C084FC"])
            fig.update_layout(
                margin=dict(l=0,r=0,t=0,b=0), height=260,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E0E0E0",size=10),
                xaxis=dict(showgrid=False,tickfont=dict(color="#9CA3AF",size=9)),
                yaxis=dict(tickfont=dict(color="#E0E0E0",size=9)),
                coloraxis_colorbar=dict(tickfont=dict(color="#E0E0E0",size=8))
            )
            fig.update_traces(marker=dict(line=dict(width=0)))
            st.plotly_chart(fig, use_container_width=True, key="top_prod")
        except Exception as e:
            st.warning(f"Chart unavailable: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        # Monthly trend
        st.markdown('<div class="chart-card"><div class="chart-label">Monthly Sales Trend</div>',
                    unsafe_allow_html=True)
        try:
            monthly = filtered_df.groupby("MonthStr")["Sales"].sum().reset_index()
            fig = px.line(monthly, x="MonthStr", y="Sales", markers=True, line_shape="spline")
            fig.update_layout(
                margin=dict(l=0,r=0,t=0,b=0), height=260,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E0E0E0",size=10),
                xaxis=dict(showgrid=False,tickfont=dict(color="#9CA3AF",size=8)),
                yaxis=dict(showgrid=False,tickfont=dict(color="#9CA3AF",size=9))
            )
            fig.update_traces(line=dict(color="#C084FC",width=2.5),
                              marker=dict(size=5,color="#00D4FF"))
            st.plotly_chart(fig, use_container_width=True, key="monthly_trend")
        except Exception as e:
            st.warning(f"Chart unavailable: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        # Profit vs Sales scatter
        st.markdown('<div class="chart-card"><div class="chart-label">Profit vs Sales</div>',
                    unsafe_allow_html=True)
        try:
            fig = px.scatter(filtered_df, x="Sales", y="Profit", color="Category",
                             opacity=0.65,
                             color_discrete_sequence=["#C084FC","#38BDF8","#86EFAC"])
            fig.update_layout(
                margin=dict(l=0,r=0,t=0,b=0), height=260,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E0E0E0",size=10),
                xaxis=dict(showgrid=False,tickfont=dict(color="#9CA3AF",size=9)),
                yaxis=dict(showgrid=False,tickfont=dict(color="#9CA3AF",size=9)),
                legend=dict(font=dict(color="#E0E0E0",size=10))
            )
            st.plotly_chart(fig, use_container_width=True, key="scatter_ps")
        except Exception as e:
            st.warning(f"Chart unavailable: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Sales by Region — full width
    st.markdown('<div class="chart-card"><div class="chart-label">Sales by Region</div>',
                unsafe_allow_html=True)
    try:
        reg = filtered_df.groupby("Region")["Sales"].sum().reset_index()
        fig = px.bar(reg, x="Region", y="Sales", color="Region",
                     text_auto=True,
                     color_discrete_sequence=["#86EFAC","#38BDF8","#FCD34D","#F9A8D4"])
        fig.update_layout(
            margin=dict(l=0,r=0,t=0,b=0), height=240,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E0E0E0",size=10),
            xaxis=dict(showgrid=False,tickfont=dict(color="#E0E0E0",size=11)),
            yaxis=dict(showgrid=False,tickfont=dict(color="#9CA3AF",size=9)),
            legend=dict(font=dict(color="#E0E0E0",size=10)),
            showlegend=False
        )
        fig.update_traces(texttemplate='$%{y:,.0f}',textposition='outside',
                          textfont=dict(color="#E0E0E0",size=10),
                          marker=dict(line=dict(width=0)))
        st.plotly_chart(fig, use_container_width=True, key="reg_sales")
    except Exception as e:
        st.warning(f"Chart unavailable: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

# ── AI Powered Insights ───────────────────────────────────────────────
if dataset_loaded and not filtered_df.empty:
    st.markdown('<div class="section-title">AI-Powered Insights</div>',
                unsafe_allow_html=True)
    try:
        best_cat      = filtered_df.groupby("Category")["Sales"].sum().idxmax()
        best_cat_val  = filtered_df.groupby("Category")["Sales"].sum().max()
        best_region   = filtered_df.groupby("Region")["Profit"].sum().idxmax()
        filtered_df["MonthYear"] = filtered_df["Order Date"].dt.strftime("%b %Y")
        peak_month    = filtered_df.groupby("MonthYear")["Sales"].sum().idxmax()
        loss_pct      = len(filtered_df[filtered_df["Profit"]<0]) / len(filtered_df) * 100

        ic1,ic2,ic3,ic4 = st.columns(4)
        with ic1:
            st.markdown(f"""
            <div class="insight-card" style="border-top-color:#22C55E;">
                <div style="font-size:10px;font-weight:700;color:#86EFAC;
                            text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">
                    Top Category
                </div>
                <div style="font-size:14px;color:#D1FAE5;font-weight:600;line-height:1.4;">
                    {best_cat} leads with ${best_cat_val:,.0f} in sales
                </div>
            </div>""", unsafe_allow_html=True)
        with ic2:
            st.markdown(f"""
            <div class="insight-card" style="border-top-color:#3B82F6;">
                <div style="font-size:10px;font-weight:700;color:#93C5FD;
                            text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">
                    Best Region
                </div>
                <div style="font-size:14px;color:#DBEAFE;font-weight:600;line-height:1.4;">
                    {best_region} shows strongest performance
                </div>
            </div>""", unsafe_allow_html=True)
        with ic3:
            st.markdown(f"""
            <div class="insight-card" style="border-top-color:#F59E0B;">
                <div style="font-size:10px;font-weight:700;color:#FCD34D;
                            text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">
                    Peak Month
                </div>
                <div style="font-size:14px;color:#FEF3C7;font-weight:600;line-height:1.4;">
                    {peak_month} has highest sales volume
                </div>
            </div>""", unsafe_allow_html=True)
        with ic4:
            st.markdown(f"""
            <div class="insight-card" style="border-top-color:#EF4444;">
                <div style="font-size:10px;font-weight:700;color:#FCA5A5;
                            text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">
                    Margin Alert
                </div>
                <div style="font-size:14px;color:#FEE2E2;font-weight:600;line-height:1.4;">
                    {loss_pct:.1f}% transactions at a loss
                </div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Insights unavailable: {e}")

st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

# ── View Detailed Data ────────────────────────────────────────────────
if dataset_loaded and not filtered_df.empty:
    with st.expander("View Detailed Data", expanded=False):
        st.markdown(f"""
        <p style="color:#6B7280;font-size:13px;margin-bottom:10px;">
            Showing <b style="color:#C084FC;">{len(filtered_df):,}</b> records
            based on current filter selection.
        </p>
        """, unsafe_allow_html=True)

        display_df = filtered_df[[
            col for col in [
                'Region','Category','Sub-Category','Product Name',
                'Sales','Profit','Quantity','Discount','Order Date'
            ] if col in filtered_df.columns
        ]].copy()

        if 'Sales'      in display_df.columns: display_df['Sales']      = display_df['Sales'].apply(lambda x: f"${x:,.0f}")
        if 'Profit'     in display_df.columns: display_df['Profit']     = display_df['Profit'].apply(lambda x: f"${x:,.0f}")
        if 'Discount'   in display_df.columns: display_df['Discount']   = display_df['Discount'].apply(lambda x: f"{x*100:.0f}%")
        if 'Order Date' in display_df.columns: display_df['Order Date'] = display_df['Order Date'].dt.strftime('%Y-%m-%d')

        st.dataframe(display_df, use_container_width=True, height=380)

st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

# ── Report Downloads ──────────────────────────────────────────────────
st.markdown('<div class="section-title">Download Reports</div>',
            unsafe_allow_html=True)
try:
    analyzer_obj = get_analyzer()
    dl1, dl2, dl3 = st.columns([1,1,2])
    with dl1:
        try:
            excel_data = generate_excel_report(analyzer_obj)
            st.download_button(
                label="Download Excel Report",
                data=excel_data,
                file_name="sales_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception: st.warning("Excel report unavailable.")
    with dl2:
        try:
            pdf_data = generate_pdf_report(analyzer_obj)
            st.download_button(
                label="Download PDF Report",
                data=pdf_data,
                file_name="sales_report.pdf",
                mime="application/pdf"
            )
        except Exception: st.warning("PDF report unavailable.")
except Exception as e:
    st.error(f"Report error: {str(e)}")

st.markdown("<br><br>", unsafe_allow_html=True)

# ── Floating Toggle Button ────────────────────────────────────────────
button_container = st.container()
with button_container:
    btn_label = "Close Assistant" if st.session_state.chat_open else "AI Assistant"
    if st.button(btn_label, key="float_toggle", type="primary"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()
button_container.float("bottom: 60px; right: 24px; width: auto;")

# ── Floating Chat Panel ───────────────────────────────────────────────
if st.session_state.chat_open:
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-header">AI Sales Assistant</div>',
                    unsafe_allow_html=True)

        if not st.session_state.chat_messages:
            st.markdown("""
            <div class="msg-bot">
                Hello. I am your AI Sales Assistant.<br>
                Ask me anything about the sales data.
            </div>""", unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_messages[-10:]:
                css     = "msg-user" if msg['role']=='user' else "msg-bot"
                content = msg['content'].replace('<','&lt;').replace('>','&gt;')
                st.markdown(f'<div class="{css}">{content}</div>',
                            unsafe_allow_html=True)

        st.markdown("&nbsp;")
        st.markdown("**Quick Questions:**")
        q1, q2 = st.columns(2)
        with q1:
            if st.button("Top Region",    key="qq1"):
                st.session_state.pending_q = "Which region has the highest sales?"; st.rerun()
            if st.button("Category",      key="qq2"):
                st.session_state.pending_q = "Which category has highest profit?";  st.rerun()
        with q2:
            if st.button("Top Products",  key="qq3"):
                st.session_state.pending_q = "What are the top 5 products?";        st.rerun()
            if st.button("Monthly Trend", key="qq4"):
                st.session_state.pending_q = "Show me the monthly sales trend";     st.rerun()

        user_input = st.chat_input("Ask about sales data...")
        if user_input:
            st.session_state.pending_q = user_input; st.rerun()

        if st.button("Clear Conversation", key="clear_btn", type="secondary"):
            clear_memory(); st.rerun()

    chat_container.float(
        "bottom: 120px; right: 24px; width: 360px; "
        "background: rgba(10,10,22,0.92); border-radius: 18px; "
        "box-shadow: 0 0 40px rgba(123,47,190,0.3); "
        "border: 1px solid rgba(123,47,190,0.3); "
        "padding: 0 14px 14px 14px; "
        "max-height: 520px; overflow-y: auto; z-index: 999; "
        "backdrop-filter: blur(20px);"
    )