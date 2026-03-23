# main_app.py
# Team 5 — Integration & Interface
# Midnight Aurora Theme + View Detailed Data

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

if 'chat_open' not in st.session_state:
    st.session_state.chat_open = False
if 'pending_q' not in st.session_state:
    st.session_state.pending_q = None
if 'app_loaded' not in st.session_state:
    st.session_state.app_loaded = False
if 'api_error' not in st.session_state:
    st.session_state.api_error = None

# ── Midnight Aurora CSS ───────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Dark background */
.stApp {
    background-color: #0E1117 !important;
}
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 100% !important;
    background-color: #0E1117 !important;
}

/* All text white on dark */
h1, h2, h3, p, span, div, label {
    color: #E0E0E0 !important;
}

/* Page title gradient */
.main-title {
    background: linear-gradient(90deg, #00D4FF, #C084FC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.5px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #161625 !important;
    border-right: 1px solid #2D2D4E !important;
}
[data-testid="stSidebar"] * {
    color: #E0E0E0 !important;
}
div[data-baseweb="select"] > div {
    background-color: #1E1E2E !important;
    color: #E0E0E0 !important;
    border: 1px solid #3D3D6E !important;
    border-radius: 8px !important;
}

/* Sidebar button */
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #7B2FBE, #5B21B6) !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    width: 100% !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #9B4FDE, #7B2FBE) !important;
}

/* KPI Cards — Dark with purple glow border */
.kpi-card {
    background-color: #1E1E2E;
    padding: 14px 8px;
    border-radius: 14px;
    border-left: 3px solid #7B2FBE;
    box-shadow: 0 0 15px rgba(123, 47, 190, 0.3);
    text-align: center;
    min-height: 85px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 0 25px rgba(123, 47, 190, 0.5);
}
.kpi-label {
    font-size: 9px;
    color: #A0A0C0 !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 700;
    margin-bottom: 6px;
    white-space: nowrap;
}
.kpi-value {
    font-size: 16px;
    font-weight: 800;
    color: #C084FC !important;
    line-height: 1.2;
}

/* Section titles */
.section-title {
    font-size: 16px;
    font-weight: 700;
    color: #00D4FF !important;
    margin: 24px 0 12px 0;
    padding-left: 10px;
    border-left: 3px solid #C084FC;
    display: block;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Chart cards */
.chart-card {
    background: #1E1E2E;
    border-radius: 14px;
    padding: 12px;
    box-shadow: 0 0 15px rgba(123, 47, 190, 0.2);
    border: 1px solid #2D2D4E;
    margin-bottom: 12px;
}

/* Download buttons */
.stDownloadButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 18px !important;
    border: none !important;
    background: linear-gradient(135deg, #7B2FBE, #5B21B6) !important;
    color: white !important;
    box-shadow: 0 0 12px rgba(123, 47, 190, 0.4) !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #9B4FDE, #7B2FBE) !important;
    transform: translateY(-1px) !important;
}

/* Primary buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7B2FBE, #5B21B6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    box-shadow: 0 0 12px rgba(123, 47, 190, 0.4) !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="secondary"] {
    background: #1E1E2E !important;
    color: #C084FC !important;
    border: 1px solid #7B2FBE !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #2D2D4E !important;
}

/* Divider */
hr {
    border: none !important;
    border-top: 1px solid #2D2D4E !important;
    margin: 1.2rem 0 !important;
}

/* Alert */
div[data-testid="stAlert"] {
    background: #1E1E2E !important;
    border: 1px solid #3D3D6E !important;
    border-radius: 12px !important;
    color: #C084FC !important;
}

/* Expander — View Detailed Data */
details {
    background: #1E1E2E !important;
    border: 1px solid #3D3D6E !important;
    border-radius: 12px !important;
}
details summary {
    color: #00D4FF !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
}
[data-testid="stExpander"] {
    background: #1E1E2E !important;
    border: 1px solid #3D3D6E !important;
    border-radius: 12px !important;
}

/* Dataframe table */
[data-testid="stDataFrame"] {
    background: #1E1E2E !important;
}
.stDataFrame th {
    background: #2D2D4E !important;
    color: #C084FC !important;
}
.stDataFrame td {
    color: #E0E0E0 !important;
}

/* Chat messages */
.msg-user {
    background: linear-gradient(135deg, #7B2FBE, #5B21B6);
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
    background: #1E1E2E;
    color: #E0E0E0;
    padding: 10px 15px;
    border-radius: 16px 16px 16px 3px;
    margin: 6px 0;
    font-size: 13px;
    word-wrap: break-word;
    text-align: left;
    border: 1px solid #3D3D6E;
    line-height: 1.5;
}
.chat-header {
    background: linear-gradient(135deg, #7B2FBE, #5B21B6);
    color: white;
    padding: 14px 18px;
    border-radius: 14px 14px 0 0;
    font-weight: 700;
    font-size: 15px;
    margin-bottom: 10px;
}

/* Chat input */
div[data-testid="stChatInput"] > div {
    border-radius: 12px !important;
    border: 1px solid #3D3D6E !important;
    background: #1E1E2E !important;
}
div[data-testid="stChatInput"] > div:focus-within {
    border-color: #7B2FBE !important;
    box-shadow: 0 0 0 3px rgba(123, 47, 190, 0.2) !important;
}

/* KPI columns */
[data-testid="stHorizontalBlock"] {
    gap: 6px !important;
}
[data-testid="column"] {
    min-width: 80px !important;
}

/* Insights panel cards */
.insight-card-green  { background: #1a3a2a; border-left: 3px solid #22c55e; border-radius: 10px; padding: 14px 16px; }
.insight-card-blue   { background: #1a2a3a; border-left: 3px solid #3b82f6; border-radius: 10px; padding: 14px 16px; }
.insight-card-olive  { background: #2a2a1a; border-left: 3px solid #84cc16; border-radius: 10px; padding: 14px 16px; }
.insight-card-red    { background: #3a1a1a; border-left: 3px solid #ef4444; border-radius: 10px; padding: 14px 16px; }
</style>
""", unsafe_allow_html=True)

# ── Startup Loading Screen ────────────────────────────────────────────
if not st.session_state.app_loaded:
    with st.spinner(""):
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;padding:100px 20px;text-align:center;
                    background:#0E1117;">
            <div style="font-size:32px;font-weight:800;margin-bottom:8px;
                        background:linear-gradient(90deg,#00D4FF,#C084FC);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                AI Sales Analytics Dashboard
            </div>
            <div style="font-size:16px;color:#A0A0C0;margin-bottom:32px;">
                Preparing your dashboard...
            </div>
            <div style="font-size:14px;color:#7B2FBE;margin:4px 0;">Loading sales dataset...</div>
            <div style="font-size:14px;color:#7B2FBE;margin:4px 0;">Initialising AI assistant...</div>
            <div style="font-size:14px;color:#7B2FBE;margin:4px 0;">Building analytics engine...</div>
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
    analyzer    = get_analyzer()
    df_raw      = analyzer.df.copy()
    if 'shipping_delay_days' in df_raw.columns and 'Shipping Delay' not in df_raw.columns:
        df_raw['Shipping Delay'] = df_raw['shipping_delay_days']
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
    "<h2 style='text-align:center;color:#C084FC !important;'>Dashboard Filters</h2>",
    unsafe_allow_html=True
)
st.sidebar.markdown(
    "<p style='text-align:center;color:#A0A0C0 !important;font-size:13px;'>Use filters to explore the dataset.</p>",
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
st.sidebar.caption("Sales Analytics Dashboard   |   Data Analysis Project")

# ── Dashboard Header ──────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:20px 0 10px 0;">
    <div class="main-title">Sales Analytics Dashboard</div>
    <p style="color:#A0A0C0 !important;font-size:14px;margin-top:4px;">
        Real-time Analytics &nbsp;•&nbsp; AI Assistant &nbsp;•&nbsp; Performance Metrics
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── 8 KPI Cards ───────────────────────────────────────────────────────
if dataset_loaded and not filtered_df.empty:
    st.markdown('<span class="section-title">Key Performance Indicators</span>',
                unsafe_allow_html=True)

    total_sales   = filtered_df['Sales'].sum()
    avg_order     = filtered_df['Sales'].mean()
    total_profit  = filtered_df['Profit'].sum()
    profit_margin = ((filtered_df['Profit'] / filtered_df['Sales']).mean() * 100
                     if not filtered_df.empty else 0)
    avg_discount  = (filtered_df['Discount'].mean() * 100
                     if not filtered_df.empty else 0)
    profit_ratio  = (total_profit / total_sales) if total_sales != 0 else 0
    total_records = len(filtered_df)

    try:
        o_date       = pd.to_datetime(filtered_df["Order Date"], dayfirst=True, errors="coerce")
        s_date       = pd.to_datetime(filtered_df["Ship Date"],  dayfirst=True, errors="coerce")
        avg_shipping = (s_date - o_date).dt.days.mean()
        if np.isnan(avg_shipping):
            avg_shipping = 0.0
    except Exception:
        avg_shipping = 0.0

    metrics = [
        ("REVENUE",       f"${total_sales/1_000_000:.1f}M"),
        ("PROFIT",        f"${total_profit/1_000:.0f}K"),
        ("ORDERS",        f"{total_records:,}"),
        ("AVG TICKET",    f"${avg_order:,.0f}"),
        ("UNITS",         f"{filtered_df['Quantity'].sum():,}" if 'Quantity' in filtered_df.columns else "N/A"),
        ("DISCOUNT",      f"{avg_discount:.1f}%"),
        ("MARGIN",        f"{profit_margin:.1f}%"),
        ("DELIVERY",      f"{avg_shipping:.1f}d"),
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
    st.markdown('<span class="section-title">AI-Powered Insights</span>',
                unsafe_allow_html=True)
    try:
        best_category = filtered_df.groupby("Category")["Sales"].sum().idxmax()
        best_cat_sales = filtered_df.groupby("Category")["Sales"].sum().max()
        best_region   = filtered_df.groupby("Region")["Profit"].sum().idxmax()
        temp          = filtered_df.copy()
        temp["Month"] = temp["Order Date"].dt.strftime("%b %Y")
        peak_month    = temp.groupby("Month")["Sales"].sum().idxmax()
        loss_orders   = len(filtered_df[filtered_df["Profit"] < 0])
        loss_pct      = (loss_orders / total_records * 100) if total_records > 0 else 0

        ic1, ic2, ic3, ic4 = st.columns(4)
        with ic1:
            st.markdown(f"""
            <div class="insight-card-green">
                <div style="font-size:12px;color:#86efac;font-weight:700;margin-bottom:4px;">
                    Top Category
                </div>
                <div style="font-size:14px;color:#bbf7d0;font-weight:600;">
                    {best_category} leads with ${best_cat_sales:,.0f} in sales
                </div>
            </div>
            """, unsafe_allow_html=True)
        with ic2:
            st.markdown(f"""
            <div class="insight-card-blue">
                <div style="font-size:12px;color:#93c5fd;font-weight:700;margin-bottom:4px;">
                    Best Region
                </div>
                <div style="font-size:14px;color:#bfdbfe;font-weight:600;">
                    {best_region} shows strongest performance
                </div>
            </div>
            """, unsafe_allow_html=True)
        with ic3:
            st.markdown(f"""
            <div class="insight-card-olive">
                <div style="font-size:12px;color:#bef264;font-weight:700;margin-bottom:4px;">
                    Peak Month
                </div>
                <div style="font-size:14px;color:#d9f99d;font-weight:600;">
                    {peak_month} has highest sales volume
                </div>
            </div>
            """, unsafe_allow_html=True)
        with ic4:
            st.markdown(f"""
            <div class="insight-card-red">
                <div style="font-size:12px;color:#fca5a5;font-weight:700;margin-bottom:4px;">
                    Margin Alert
                </div>
                <div style="font-size:14px;color:#fecaca;font-weight:600;">
                    {loss_pct:.1f}% transactions at a loss
                </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Insights unavailable: {e}")

elif dataset_loaded and filtered_df.empty:
    st.info("No data matches the selected filters. Please adjust the filters in the sidebar.")

st.markdown("---")

# ── View Detailed Data ────────────────────────────────────────────────
if dataset_loaded and not filtered_df.empty:
    with st.expander("View Detailed Data", expanded=False):
        st.markdown(f"""
        <p style="color:#A0A0C0;font-size:13px;margin-bottom:12px;">
            Showing <b style="color:#C084FC;">{len(filtered_df):,}</b> records
            based on current filter selection.
        </p>
        """, unsafe_allow_html=True)

        # Build display dataframe with formatted columns
        display_df = filtered_df[[
            col for col in [
                'Region', 'Category', 'Sub-Category', 'Product Name',
                'Sales', 'Profit', 'Quantity', 'Discount', 'Order Date'
            ] if col in filtered_df.columns
        ]].copy()

        # Format numeric columns
        if 'Sales' in display_df.columns:
            display_df['Sales'] = display_df['Sales'].apply(lambda x: f"${x:,.0f}")
        if 'Profit' in display_df.columns:
            display_df['Profit'] = display_df['Profit'].apply(lambda x: f"${x:,.0f}")
        if 'Discount' in display_df.columns:
            display_df['Discount'] = display_df['Discount'].apply(lambda x: f"{x*100:.0f}%")
        if 'Order Date' in display_df.columns:
            display_df['Order Date'] = display_df['Order Date'].dt.strftime('%Y-%m-%d')

        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )

st.markdown("---")

# ── Report Downloads ──────────────────────────────────────────────────
st.markdown('<span class="section-title">Download Reports</span>',
            unsafe_allow_html=True)
try:
    dl1, dl2, dl3 = st.columns([1, 1, 2])
    with dl1:
        try:
            excel_data = generate_excel_report(analyzer)
            st.download_button(
                label="Download Excel Report",
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
                label="Download PDF Report",
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
    btn_label = "Close Assistant" if st.session_state.chat_open else "AI Assistant"
    if st.button(btn_label, key="float_toggle", type="primary"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()
button_container.float("bottom: 60px; right: 24px; width: auto;")

# ── Floating Chat Panel ───────────────────────────────────────────────
if st.session_state.chat_open:
    chat_container = st.container()
    with chat_container:
        st.markdown("""
        <div class="chat-header">AI Sales Assistant</div>
        """, unsafe_allow_html=True)

        if not st.session_state.chat_messages:
            st.markdown("""
            <div class="msg-bot">
                Hello. I am your AI Sales Assistant.<br>
                Ask me anything about the sales data.
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
            if st.button("Top Region", key="qq1"):
                st.session_state.pending_q = "Which region has the highest sales?"
                st.rerun()
            if st.button("Category", key="qq2"):
                st.session_state.pending_q = "Which category has highest profit?"
                st.rerun()
        with q2:
            if st.button("Top Products", key="qq3"):
                st.session_state.pending_q = "What are the top 5 products?"
                st.rerun()
            if st.button("Monthly Trend", key="qq4"):
                st.session_state.pending_q = "Show me the monthly sales trend"
                st.rerun()

        user_input = st.chat_input("Ask about sales data...")
        if user_input:
            st.session_state.pending_q = user_input
            st.rerun()

        if st.button("Clear Conversation", key="clear_btn", type="secondary"):
            clear_memory()
            st.rerun()

    chat_container.float(
        "bottom: 120px; right: 24px; width: 360px; "
        "background-color: #1E1E2E; border-radius: 18px; "
        "box-shadow: 0 0 30px rgba(123,47,190,0.3); "
        "border: 1px solid #3D3D6E; padding: 0 14px 14px 14px; "
        "max-height: 520px; overflow-y: auto; z-index: 999;"
    )