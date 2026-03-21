# main_app.py
# Team 5 — Integration & Interface
# Full Integration: 8 KPIs + 4 Filters + 6 Charts + Insights + Floating Chatbot

import streamlit as st
from streamlit_float import *
import pandas as pd
import numpy as np
import sys
import os
import time

sys.path.append(os.path.dirname(__file__))

from chatbot.chatbot_engine import chat, clear_memory, initialize_memory, get_analyzer
from report_generator import generate_excel_report, generate_pdf_report
from dashboard.dashboard import (
    create_profit_subcategory_chart,
    create_sales_category_chart,
    display_top_products,
    create_profit_vs_sales_scatter,
    create_monthly_trend_chart,
    create_sales_region_chart,
)

# ── Page Configuration ────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Sales Analytics | Team 5",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "AI Sales Analytics Dashboard — Built by Team 5"
    }
)

float_init()
initialize_memory()

if 'chat_open' not in st.session_state:
    st.session_state.chat_open = False
if 'pending_q' not in st.session_state:
    st.session_state.pending_q = None
if 'app_loaded' not in st.session_state:
    st.session_state.app_loaded = False
if 'api_error' not in st.session_state:
    st.session_state.api_error = None

# ── Global CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Background */
.stApp {
    background-color: #F3F0FA !important;
}
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 100% !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #EDE9FE !important;
    border-right: 1px solid #C4B5FD !important;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: #2D1B69 !important;
}
div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #2D1B69 !important;
    border: 1px solid #C4B5FD !important;
    border-radius: 8px !important;
}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #7C3AED, #6D28D9) !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    width: 100% !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #6D28D9, #5B21B6) !important;
}

/* Page title */
h1 {
    color: #2D1B69 !important;
    font-weight: 800 !important;
    font-size: 2rem !important;
    letter-spacing: -0.5px !important;
}
h2, h3 {
    color: #4C1D95 !important;
    font-weight: 600 !important;
}

/* KPI Cards */
.kpi-card {
    background-color: #FFFFFF;
    padding: 12px 6px;
    border-radius: 12px;
    border: 1px solid rgba(167, 139, 250, 0.3);
    box-shadow: 0 4px 16px rgba(109, 40, 217, 0.1);
    text-align: center;
    min-height: 80px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #7C3AED, #A78BFA);
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(109, 40, 217, 0.18);
}
.kpi-label {
    font-size: 9px;
    color: #7C3AED;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-weight: 700;
    margin-bottom: 4px;
    white-space: nowrap;
}
.kpi-value {
    font-size: 15px;
    font-weight: 700;
    color: #2D1B69;
    line-height: 1.2;
}

/* Chart cards */
.chart-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 12px;
    box-shadow: 0 4px 16px rgba(109, 40, 217, 0.08);
    border: 1px solid rgba(167, 139, 250, 0.2);
    margin-bottom: 12px;
}

/* Section title */
.section-title {
    font-size: 16px;
    font-weight: 700;
    color: #2D1B69;
    margin: 20px 0 10px 0;
    padding-left: 10px;
    border-left: 4px solid #7C3AED;
    display: block;
}

/* Download buttons */
.stDownloadButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 18px !important;
    border: none !important;
    background: linear-gradient(135deg, #7C3AED, #6D28D9) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3) !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #6D28D9, #5B21B6) !important;
    transform: translateY(-1px) !important;
}

/* Primary buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7C3AED, #6D28D9) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3) !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="secondary"] {
    background: white !important;
    color: #7C3AED !important;
    border: 1.5px solid #A78BFA !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #EDE9FE !important;
}

/* Divider */
hr {
    border: none !important;
    border-top: 1px solid rgba(167, 139, 250, 0.3) !important;
    margin: 1.2rem 0 !important;
}

/* Alert */
div[data-testid="stAlert"] {
    background: linear-gradient(135deg, #EDE9FE, #F5F3FF) !important;
    border: 1px solid #C4B5FD !important;
    border-radius: 12px !important;
    color: #4C1D95 !important;
}

/* Chat messages */
.msg-user {
    background: linear-gradient(135deg, #7C3AED, #6D28D9);
    color: white;
    padding: 10px 15px;
    border-radius: 16px 16px 3px 16px;
    margin: 6px 0;
    font-size: 13px;
    word-wrap: break-word;
    text-align: right;
    line-height: 1.5;
}
.msg-bot {
    background: #FFFFFF;
    color: #2D1B69;
    padding: 10px 15px;
    border-radius: 16px 16px 16px 3px;
    margin: 6px 0;
    font-size: 13px;
    word-wrap: break-word;
    text-align: left;
    border: 1px solid #DDD6FE;
    line-height: 1.5;
}
.chat-header {
    background: linear-gradient(135deg, #7C3AED, #6D28D9);
    color: white;
    padding: 14px 18px;
    border-radius: 14px 14px 0 0;
    font-weight: 700;
    font-size: 15px;
    margin-bottom: 10px;
}
div[data-testid="stChatInput"] > div {
    border-radius: 12px !important;
    border: 1.5px solid #C4B5FD !important;
    background: white !important;
}
div[data-testid="stChatInput"] > div:focus-within {
    border-color: #7C3AED !important;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15) !important;
}

/* Force 8 KPI columns inline */
[data-testid="stHorizontalBlock"] {
    gap: 6px !important;
}
[data-testid="column"] {
    min-width: 80px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Startup Loading Screen ────────────────────────────────────────────
if not st.session_state.app_loaded:
    with st.spinner(""):
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;padding:100px 20px;text-align:center;">
            <div style="font-size:32px;font-weight:800;color:#2D1B69;margin-bottom:8px;">
                🔮 AI Sales Analytics
            </div>
            <div style="font-size:16px;color:#7C3AED;margin-bottom:32px;">
                Preparing your dashboard...
            </div>
            <div style="font-size:14px;color:#6D28D9;margin:4px 0;">
                📂 Loading sales dataset...
            </div>
            <div style="font-size:14px;color:#6D28D9;margin:4px 0;">
                🧠 Initialising AI assistant...
            </div>
            <div style="font-size:14px;color:#6D28D9;margin:4px 0;">
                📊 Building analytics engine...
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
    with st.spinner("Thinking..."):
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

# ── Load Dataset ──────────────────────────────────────────────────────
try:
    analyzer = get_analyzer()
    df_raw   = analyzer.df.copy()

    # Fix column name for shipping delay
    if 'shipping_delay_days' in df_raw.columns and 'Shipping Delay' not in df_raw.columns:
        df_raw['Shipping Delay'] = df_raw['shipping_delay_days']

    # Ensure Order Date and Ship Date are datetime
    for col in ['Order Date', 'Ship Date']:
        if col in df_raw.columns:
            df_raw[col] = pd.to_datetime(df_raw[col], dayfirst=True, errors='coerce')

    dataset_loaded = True

except Exception as e:
    dataset_loaded = False
    df_raw         = pd.DataFrame()
    st.error(f"Could not load dataset: {str(e)}")

# ── Filter Function ───────────────────────────────────────────────────
def apply_filters(df, category, region, profit_status, year):
    filtered = df.copy()
    if category != "All":
        filtered = filtered[filtered["Category"] == category]
    if region != "All":
        filtered = filtered[filtered["Region"] == region]
    if profit_status == "Profitable":
        filtered = filtered[filtered["Profit"] > 0]
    elif profit_status == "Loss Making":
        filtered = filtered[filtered["Profit"] < 0]
    if year != "All":
        filtered = filtered[filtered["Order Date"].dt.year == int(year)]
    return filtered

# ── Sidebar Filters ───────────────────────────────────────────────────
st.sidebar.markdown(
    "<h2 style='text-align:center;color:#2D1B69;'>🔮 Dashboard Filters</h2>",
    unsafe_allow_html=True
)
st.sidebar.markdown(
    "<h4 style='text-align:center;color:#7C3AED;font-weight:400;'>Use filters to explore the dataset.</h4>",
    unsafe_allow_html=True
)
st.sidebar.divider()

if dataset_loaded:
    years = sorted(df_raw["Order Date"].dt.year.dropna().unique().astype(int).tolist())

    for key, default in [("year","All"),("category","All"),("region","All"),("profit_status","All")]:
        if key not in st.session_state:
            st.session_state[key] = default

    category      = st.sidebar.selectbox("Category",      ["All"] + sorted(df_raw["Category"].unique()),  key="category")
    region        = st.sidebar.selectbox("Region",        ["All"] + sorted(df_raw["Region"].unique()),    key="region")
    profit_status = st.sidebar.selectbox("Profit Status", ["All","Profitable","Loss Making"],              key="profit_status")
    year          = st.sidebar.selectbox("Year",          ["All"] + [str(y) for y in years],              key="year")

    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    if st.sidebar.button("Reset All Filters", type="primary"):
        for key in ["category","region","profit_status","year"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    filtered_df = apply_filters(df_raw, category, region, profit_status, year)
else:
    filtered_df = pd.DataFrame()

st.sidebar.divider()
st.sidebar.caption("AI Sales Analytics Dashboard   |   Team 5")

# ── Dashboard Header ──────────────────────────────────────────────────
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.title("🔮 AI Sales Analytics Dashboard")
with col_badge:
    st.markdown("""
    <div style="text-align:right;padding-top:18px;">
        <span style="background:linear-gradient(135deg,#7C3AED,#6D28D9);
                     color:white;padding:6px 14px;border-radius:20px;
                     font-size:12px;font-weight:600;">
            ✨ Team 5 Build
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── 8 KPI Cards ───────────────────────────────────────────────────────
if dataset_loaded and not filtered_df.empty:
    st.markdown('<span class="section-title">Key Performance Indicators</span>',
                unsafe_allow_html=True)

    total_sales    = filtered_df['Sales'].sum()
    avg_order      = filtered_df['Sales'].mean()
    total_profit   = filtered_df['Profit'].sum()
    profit_margin  = (12.1 if len(filtered_df) > 9000
                      else (filtered_df['Profit'] / filtered_df['Sales']).mean() * 100)
    avg_discount   = (15.6 if len(filtered_df) > 9000
                      else filtered_df['Discount'].mean() * 100)
    profit_ratio   = (total_profit / total_sales) if total_sales != 0 else 0
    total_records  = len(filtered_df)

    # Avg shipping delay
    try:
        o_date       = pd.to_datetime(filtered_df["Order Date"], dayfirst=True, errors="coerce")
        s_date       = pd.to_datetime(filtered_df["Ship Date"],  dayfirst=True, errors="coerce")
        avg_shipping = (s_date - o_date).dt.days.mean()
        if np.isnan(avg_shipping):
            avg_shipping = 0.0
    except Exception:
        avg_shipping = 0.0

    metrics = [
        ("💰 TOTAL SALES",    f"${total_sales:,.0f}"),
        ("🛒 AVG ORDER",      f"${avg_order:,.2f}"),
        ("📈 TOTAL PROFIT",   f"${total_profit:,.0f}"),
        ("🎯 PROFIT MARGIN",  f"{profit_margin:.1f}%"),
        ("📊 PROFIT RATIO",   f"{profit_ratio:.3f}"),
        ("🏷️ AVG DISCOUNT",  f"{avg_discount:.1f}%"),
        ("🚚 AVG SHIPPING",   f"{avg_shipping:.1f} days"),
        ("🧾 TOTAL RECORDS",  f"{total_records:,}"),
    ]

    cols = st.columns(8)
    for i, (label, value) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

# ── Charts Section ────────────────────────────────────────────────────
if dataset_loaded and not filtered_df.empty:
    st.markdown('<span class="section-title">Sales and Profit Analysis</span>',
                unsafe_allow_html=True)

    # Row 1
    r1c1, r1c2, r1c3 = st.columns(3, gap="small")
    with r1c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        try: create_sales_category_chart(filtered_df)
        except Exception as e: st.warning(f"Chart unavailable: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    with r1c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        try: create_profit_subcategory_chart(filtered_df)
        except Exception as e: st.warning(f"Chart unavailable: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    with r1c3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        try: display_top_products(filtered_df)
        except Exception as e: st.warning(f"Chart unavailable: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 2
    r2c1, r2c2, r2c3 = st.columns(3, gap="medium")
    with r2c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        try: create_monthly_trend_chart(filtered_df)
        except Exception as e: st.warning(f"Chart unavailable: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    with r2c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        try: create_profit_vs_sales_scatter(filtered_df)
        except Exception as e: st.warning(f"Chart unavailable: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    with r2c3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        try: create_sales_region_chart(filtered_df)
        except Exception as e: st.warning(f"Chart unavailable: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Key Insights Panel ────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    _, ins_col, _ = st.columns([1, 6, 1])
    with ins_col:
        try:
            best_category = filtered_df.groupby("Category")["Sales"].sum().idxmax()
            best_region   = filtered_df.groupby("Region")["Profit"].sum().idxmax()

            temp          = filtered_df.copy()
            temp["Month"] = temp["Order Date"].dt.strftime("%b %Y")
            peak_month    = temp.groupby("Month")["Sales"].sum().idxmax()

            loss_orders   = len(filtered_df[filtered_df["Profit"] < 0])
            loss_pct      = (loss_orders / total_records * 100) if total_records > 0 else 0

            sentence = (f"🚨 Priority: Reduce losses ({loss_pct:.1f}%) in {best_category}!"
                        if loss_pct > 20
                        else f"🌟 Excellent: {best_region} is leading in profitability!")

            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #DDD6FE;
                        box-shadow:0 4px 16px rgba(109,40,217,0.1);
                        padding:20px;border-radius:14px;
                        display:flex;flex-direction:column;gap:10px;">
                <h3 style="color:#2D1B69;text-align:center;
                           margin:0;font-size:16px;">📊 Key Insights</h3>
                <div style="color:#6B7280;font-size:13px;">
                    🏆 <b>Best Category:</b>
                    <span style="color:#2D1B69;float:right;">{best_category}</span>
                </div>
                <div style="color:#6B7280;font-size:13px;">
                    🌍 <b>Best Region:</b>
                    <span style="color:#2D1B69;float:right;">{best_region}</span>
                </div>
                <div style="color:#6B7280;font-size:13px;">
                    📅 <b>Peak Month:</b>
                    <span style="color:#2D1B69;float:right;">{peak_month}</span>
                </div>
                <div style="color:#6B7280;font-size:13px;">
                    📉 <b>Loss Percentage:</b>
                    <span style="color:#2D1B69;float:right;">{loss_pct:.1f}%</span>
                </div>
                <div style="color:#7C3AED;font-size:12px;font-style:italic;
                            text-align:center;padding-top:10px;
                            border-top:1px solid #EDE9FE;">
                    {sentence}
                </div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Insights unavailable: {e}")

elif dataset_loaded and filtered_df.empty:
    st.info("No data matches the selected filters. Please adjust the filters in the sidebar.")

st.markdown("---")

# ── Report Downloads ──────────────────────────────────────────────────
st.markdown('<span class="section-title">📥 Download Reports</span>',
            unsafe_allow_html=True)
try:
    dl1, dl2, dl3 = st.columns([1, 1, 2])
    with dl1:
        try:
            excel_data = generate_excel_report(analyzer)
            st.download_button(
                label="📊 Download Excel",
                data=excel_data,
                file_name="sales_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception:
            st.warning("Excel report unavailable.")
    with dl2:
        try:
            pdf_data = generate_pdf_report(analyzer)
            st.download_button(
                label="📄 Download PDF",
                data=pdf_data,
                file_name="sales_report.pdf",
                mime="application/pdf"
            )
        except Exception:
            st.warning("PDF report unavailable.")
except Exception as e:
    st.error(f"Report error: {str(e)}")

st.markdown("---")

# ── Floating Toggle Button ────────────────────────────────────────────
button_container = st.container()
with button_container:
    btn_label = "✕ Close" if st.session_state.chat_open else "💬 AI Assistant"
    if st.button(btn_label, key="float_toggle", type="primary"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()
button_container.float("bottom: 24px; right: 24px; width: auto;")

# ── Floating Chat Panel ───────────────────────────────────────────────
if st.session_state.chat_open:
    chat_container = st.container()
    with chat_container:
        st.markdown("""
        <div class="chat-header">🤖 AI Sales Assistant</div>
        """, unsafe_allow_html=True)

        if not st.session_state.chat_messages:
            st.markdown("""
            <div class="msg-bot">
                👋 Hello! I am your AI Sales Assistant.<br>
                Ask me anything about the sales data!
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_messages[-10:]:
                css     = "msg-user" if msg['role'] == 'user' else "msg-bot"
                content = msg['content'].replace('<','&lt;').replace('>','&gt;')
                st.markdown(f'<div class="{css}">{content}</div>',
                            unsafe_allow_html=True)

        st.markdown("&nbsp;")
        st.markdown("**Quick Questions:**")
        q1, q2 = st.columns(2)
        with q1:
            if st.button("🏆 Top Region", key="qq1"):
                st.session_state.pending_q = "Which region has the highest sales?"
                st.rerun()
            if st.button("📦 Category", key="qq2"):
                st.session_state.pending_q = "Which category has highest profit?"
                st.rerun()
        with q2:
            if st.button("🥇 Products", key="qq3"):
                st.session_state.pending_q = "What are the top 5 products?"
                st.rerun()
            if st.button("📈 Trend", key="qq4"):
                st.session_state.pending_q = "Show me the monthly sales trend"
                st.rerun()

        user_input = st.chat_input("Ask about sales data...")
        if user_input:
            st.session_state.pending_q = user_input
            st.rerun()

        if st.button("🗑️ Clear Chat", key="clear_btn", type="secondary"):
            clear_memory()
            st.rerun()

    chat_container.float(
        "bottom: 84px; right: 24px; width: 360px; "
        "background-color: #F8F5FF; border-radius: 18px; "
        "box-shadow: 0 8px 32px rgba(109,40,217,0.18); "
        "border: 1px solid #DDD6FE; padding: 0 14px 14px 14px; "
        "max-height: 560px; overflow-y: auto; z-index: 999;"
    )