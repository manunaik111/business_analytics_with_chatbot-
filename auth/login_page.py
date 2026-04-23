# auth/login_page.py
# Login page UI — Midnight Aurora theme

import streamlit as st
from .auth_manager import verify_login, login_user, init_session, init_db

def show_login_page():
    """Render the full-screen login page."""
    init_db()
    init_session()

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* Fix material icons showing as text */
    .material-icons,
    .material-symbols-outlined,
    .material-symbols-rounded,
    .material-symbols-sharp {
        font-family: "Material Symbols Rounded","Material Symbols Outlined",
                     "Material Icons", sans-serif !important;
    }

    * { font-family: 'Inter', sans-serif !important; }

    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
    header     { visibility: hidden; }

    .stApp {
        background-color: #080B14 !important;
        background-image:
            radial-gradient(ellipse at 20% 20%, rgba(123,47,190,0.10) 0%, transparent 55%),
            radial-gradient(ellipse at 80% 80%, rgba(0,212,255,0.06) 0%, transparent 55%);
    }

    /* Remove default Streamlit container styling that causes empty box */
    .block-container {
        max-width: 460px !important;
        padding-top: 4rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Hide any stray empty containers */
    [data-testid="stVerticalBlock"] > div:empty { display: none !important; }

    /* Card */
    .login-card {
        background: rgba(14, 14, 30, 0.88);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border-radius: 24px;
        border: 1px solid rgba(123,47,190,0.30);
        box-shadow:
            0 24px 64px rgba(0,0,0,0.55),
            0 0 40px rgba(123,47,190,0.12),
            inset 0 1px 0 rgba(255,255,255,0.04);
        padding: 36px 36px 28px 36px;
        margin-bottom: 0;
    }
    .login-logo {
        font-size: 2.8rem;
        text-align: center;
        margin-bottom: 6px;
        line-height: 1;
    }
    .login-title {
        background: linear-gradient(270deg, #00D4FF, #C084FC, #818CF8, #00D4FF);
        background-size: 300% 300%;
        animation: gradientShift 5s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.75rem;
        font-weight: 900;
        text-align: center;
        letter-spacing: -0.5px;
        margin-bottom: 4px;
    }
    .login-sub {
        color: #4B5563 !important;
        font-size: 11px;
        text-align: center;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-bottom: 0;
    }
    .login-divider {
        height: 1px;
        background: linear-gradient(90deg,
            transparent, rgba(123,47,190,0.7), rgba(0,212,255,0.7), transparent);
        margin: 22px 0 18px 0;
        border: none;
    }
    @keyframes gradientShift {
        0%   { background-position: 0% 50%;   }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%;   }
    }

    /* Inputs */
    div[data-baseweb="input"] > div {
        background: rgba(18,18,40,0.9) !important;
        border: 1px solid rgba(123,47,190,0.35) !important;
        border-radius: 10px !important;
        color: #E0E0E0 !important;
    }
    div[data-baseweb="input"] > div:focus-within {
        border-color: #7B2FBE !important;
        box-shadow: 0 0 0 3px rgba(123,47,190,0.18) !important;
    }
    div[data-baseweb="input"] input {
        color: #E0E0E0 !important;
        background: transparent !important;
    }
    label[data-testid="stWidgetLabel"] p {
        color: #9CA3AF !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }

    /* Login button — full width fix */
    div[data-testid="stButton"] {
        width: 100% !important;
    }
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #7B2FBE, #5B21B6) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 14px 0 !important;
        width: 100% !important;
        min-height: 48px !important;
        box-shadow: 0 0 20px rgba(123,47,190,0.40) !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.5px !important;
        margin-top: 8px !important;
    }
    div[data-testid="stButton"] > button:hover {
        box-shadow: 0 0 32px rgba(123,47,190,0.65) !important;
        transform: translateY(-2px) !important;
    }

    /* Alert */
    div[data-testid="stAlert"] {
        background: rgba(18,18,35,0.75) !important;
        border: 1px solid rgba(239,68,68,0.40) !important;
        border-radius: 10px !important;
        backdrop-filter: blur(10px) !important;
    }

    /* Hint box */
    .hint-box {
        background: rgba(123,47,190,0.08);
        border: 1px solid rgba(123,47,190,0.22);
        border-radius: 10px;
        padding: 12px 16px;
        margin-top: 16px;
        font-size: 12px;
        color: #6B7280 !important;
        text-align: center;
        line-height: 1.8;
    }
    .hint-box b { color: #C084FC !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Login card — all inside one HTML block to avoid Streamlit inserting empty divs ──
    st.markdown("""
    <div class="login-card">
        <div class="login-title">Sales Analytics</div>
        <div class="login-sub">AI-Powered Business Intelligence</div>
        <div class="login-divider"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Inputs and button rendered by Streamlit (inside the visual card area via CSS) ──
    email    = st.text_input("Email Address", placeholder="you@company.com",   key="login_email")
    password = st.text_input("Password",      placeholder="Enter your password",
                             type="password", key="login_password")

    if st.button("Sign In", key="login_btn", type="primary"):
        if not email or not password:
            st.error("Please enter both email and password.")
        else:
            success, result = verify_login(email, password)
            if success:
                login_user(result)
                st.rerun()
            else:
                st.error(result)

    st.markdown("""
    <div class="hint-box">
        Default Admin &nbsp;→&nbsp; <b>admin@sales.com</b> &nbsp;/&nbsp; <b>Admin@1234</b><br>
        <span style="font-size:10px;">Change password after first login</span>
    </div>
    """, unsafe_allow_html=True)