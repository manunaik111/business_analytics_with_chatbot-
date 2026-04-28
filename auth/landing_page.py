# auth/landing_page.py
# Public landing page — shown before login/register — Midnight Aurora theme

import streamlit as st
from .loading import wrap_page_fade


def show_landing_page():
    """Render the public-facing landing page."""

    wrap_page_fade()

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    * { font-family: 'Inter', sans-serif !important; }

    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
    header     { visibility: hidden; }

    .stApp {
        background-color: #080B14 !important;
        background-image:
            radial-gradient(ellipse at 10% 10%, rgba(123,47,190,0.13) 0%, transparent 50%),
            radial-gradient(ellipse at 90% 90%, rgba(0,212,255,0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 80%, rgba(91,33,182,0.06) 0%, transparent 45%);
    }

    .block-container {
        max-width: 900px !important;
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        margin: 0 auto !important;
        background: transparent !important;
    }

    /* ── Animated background grid ── */
    .grid-bg {
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(rgba(123,47,190,0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(123,47,190,0.04) 1px, transparent 1px);
        background-size: 48px 48px;
        pointer-events: none;
        z-index: 0;
    }

    /* ── Hero section ── */
    .hero-wrap {
        text-align: center;
        padding: 20px 0 40px 0;
        position: relative;
        z-index: 1;
    }
    .hero-eyebrow {
        display: inline-block;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #7B2FBE !important;
        background: rgba(123,47,190,0.10);
        border: 1px solid rgba(123,47,190,0.28);
        border-radius: 20px;
        padding: 5px 16px;
        margin-bottom: 22px;
    }
    .hero-title {
        background: linear-gradient(270deg, #00D4FF, #C084FC, #818CF8, #38BDF8, #00D4FF);
        background-size: 400% 400%;
        animation: gradientShift 6s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: clamp(2.4rem, 5vw, 3.6rem);
        font-weight: 900;
        letter-spacing: -2px;
        line-height: 1.1;
        margin-bottom: 18px;
    }
    .hero-desc {
        color: #6B7280 !important;
        font-size: 16px;
        line-height: 1.7;
        max-width: 560px;
        margin: 0 auto 36px auto;
        font-weight: 400;
    }
    .hero-desc b { color: #9CA3AF !important; }

    @keyframes gradientShift {
        0%   { background-position: 0% 50%;   }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%;   }
    }

    /* ── CTA Buttons ── */
    .cta-row {
        display: flex;
        gap: 14px;
        justify-content: center;
        flex-wrap: wrap;
        margin-bottom: 14px;
    }

    /* Primary — Sign In */
    div[data-testid="stButton"]:has(button[data-testid="land_signin"]) > button,
    button[key="land_signin"] {
        background: linear-gradient(135deg, #7B2FBE, #5B21B6) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 13px 36px !important;
        min-height: 48px !important;
        box-shadow: 0 0 24px rgba(123,47,190,0.40) !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.3px !important;
    }

    /* ── Stats strip ── */
    .stats-strip {
        display: flex;
        justify-content: center;
        gap: 40px;
        flex-wrap: wrap;
        margin: 14px 0 48px 0;
    }
    .stat-item { text-align: center; }
    .stat-num {
        font-size: 1.7rem;
        font-weight: 900;
        background: linear-gradient(135deg, #C084FC, #00D4FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.1;
    }
    .stat-label {
        font-size: 10px;
        font-weight: 600;
        color: #4B5563 !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-top: 2px;
    }

    /* ── Glow divider ── */
    .glow-divider {
        height: 1px;
        background: linear-gradient(90deg,
            transparent, rgba(123,47,190,0.8), rgba(0,212,255,0.8), transparent);
        margin: 0 0 44px 0;
        border: none;
        box-shadow: 0 0 12px rgba(123,47,190,0.25);
    }

    /* ── Feature cards ── */
    .features-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-bottom: 44px;
    }
    @media (max-width: 700px) {
        .features-grid { grid-template-columns: 1fr; }
    }
    .feature-card {
        background: rgba(14,14,30,0.80);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 18px;
        border: 1px solid rgba(123,47,190,0.18);
        padding: 24px 22px;
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: var(--card-accent, linear-gradient(90deg, #7B2FBE, #00D4FF));
        border-radius: 18px 18px 0 0;
    }
    .feature-card:hover {
        border-color: rgba(123,47,190,0.38);
        box-shadow: 0 12px 40px rgba(0,0,0,0.40), 0 0 20px rgba(123,47,190,0.15);
        transform: translateY(-3px);
    }
    .feature-icon {
        font-size: 26px;
        margin-bottom: 12px;
        line-height: 1;
    }
    .feature-title {
        font-size: 14px;
        font-weight: 700;
        color: #E0E0E0 !important;
        margin-bottom: 6px;
        letter-spacing: -0.2px;
    }
    .feature-desc {
        font-size: 12px;
        color: #6B7280 !important;
        line-height: 1.65;
    }

    /* ── Role cards ── */
    .roles-section {
        margin-bottom: 44px;
    }
    .section-label {
        font-size: 10px;
        font-weight: 700;
        color: #4B5563 !important;
        letter-spacing: 3px;
        text-transform: uppercase;
        text-align: center;
        margin-bottom: 20px;
    }
    .roles-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
    }
    @media (max-width: 700px) {
        .roles-grid { grid-template-columns: repeat(2, 1fr); }
    }
    .role-chip {
        background: rgba(14,14,30,0.75);
        border-radius: 12px;
        border: 1px solid rgba(123,47,190,0.15);
        padding: 14px 10px;
        text-align: center;
    }
    .role-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        margin: 0 auto 8px auto;
    }
    .role-name {
        font-size: 11px;
        font-weight: 700;
        color: #D1D5DB !important;
        margin-bottom: 4px;
    }
    .role-perm {
        font-size: 10px;
        color: #4B5563 !important;
        line-height: 1.4;
    }

    /* ── Footer strip ── */
    .land-footer {
        text-align: center;
        padding-top: 24px;
        border-top: 1px solid rgba(123,47,190,0.12);
    }
    .land-footer p {
        font-size: 11px;
        color: #374151 !important;
        letter-spacing: 1px;
    }
    </style>

    <!-- Subtle grid overlay -->
    <div class="grid-bg"></div>
    """, unsafe_allow_html=True)

    # ── Hero ──────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-eyebrow">✦ AI-Powered Business Intelligence</div>
        <div class="hero-title">Sales Analytics<br>Dashboard</div>
        <div class="hero-desc">
            Unlock <b>real-time insights</b> from your sales data.
            Interactive charts, AI chat assistant, automated reports —
            everything your team needs to make smarter decisions.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA Buttons ───────────────────────────────────────────────────
    col_l, col_c1, col_c2, col_r = st.columns([1, 1.2, 1.2, 1])
    with col_c1:
        if st.button("🔐  Sign In", key="land_signin", type="primary", use_container_width=True):
            st.session_state.current_page = "login"
            st.rerun()
    with col_c2:
        if st.button("✦  Register Free", key="land_register", use_container_width=True):
            st.session_state.current_page = "register"
            st.rerun()

    # ── Stats ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="stats-strip">
        <div class="stat-item">
            <div class="stat-num">5+</div>
            <div class="stat-label">Role Levels</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">AI</div>
            <div class="stat-label">Chat Assistant</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">2</div>
            <div class="stat-label">Report Formats</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">∞</div>
            <div class="stat-label">Data Insights</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    # ── Features ──────────────────────────────────────────────────────
    import streamlit.components.v1 as components
    components.html("""
    <style>
    * { font-family: Inter, sans-serif; box-sizing: border-box; margin: 0; padding: 0; }
    body { background: transparent; }
    .features-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
    }
    .feature-card {
        background: rgba(14,14,30,0.95);
        border-radius: 18px;
        border: 1px solid rgba(123,47,190,0.25);
        padding: 24px 22px 20px 22px;
        position: relative;
        overflow: hidden;
    }
    .fc-bar { position: absolute; top: 0; left: 0; right: 0; height: 2px; border-radius: 18px 18px 0 0; }
    .feature-icon { font-size: 26px; margin-bottom: 12px; margin-top: 6px; line-height: 1; }
    .feature-title { font-size: 14px; font-weight: 700; color: #E0E0E0; margin-bottom: 6px; }
    .feature-desc  { font-size: 12px; color: #6B7280; line-height: 1.65; }
    </style>
    <div class="features-grid">
        <div class="feature-card">
            <div class="fc-bar" style="background:linear-gradient(90deg,#7B2FBE,#C084FC);"></div>
            <div class="feature-icon">&#128202;</div>
            <div class="feature-title">Interactive Dashboard</div>
            <div class="feature-desc">KPI cards, trend charts, category breakdowns and regional heatmaps — all filterable in real time.</div>
        </div>
        <div class="feature-card">
            <div class="fc-bar" style="background:linear-gradient(90deg,#0891B2,#00D4FF);"></div>
            <div class="feature-icon">&#129302;</div>
            <div class="feature-title">AI Chat Assistant</div>
            <div class="feature-desc">Ask natural-language questions about your data and get instant, context-aware answers powered by Groq AI.</div>
        </div>
        <div class="feature-card">
            <div class="fc-bar" style="background:linear-gradient(90deg,#059669,#34D399);"></div>
            <div class="feature-icon">&#128229;</div>
            <div class="feature-title">Automated Reports</div>
            <div class="feature-desc">One-click Excel and PDF report generation with full charts, summaries, and data exports.</div>
        </div>
        <div class="feature-card">
            <div class="fc-bar" style="background:linear-gradient(90deg,#B45309,#F59E0B);"></div>
            <div class="feature-icon">&#128274;</div>
            <div class="feature-title">Role-Based Access</div>
            <div class="feature-desc">Five permission tiers — Admin, Sales Manager, Analyst, Executive, and Viewer — keep data secure.</div>
        </div>
        <div class="feature-card">
            <div class="fc-bar" style="background:linear-gradient(90deg,#BE185D,#F472B6);"></div>
            <div class="feature-icon">&#128228;</div>
            <div class="feature-title">Data Upload</div>
            <div class="feature-desc">Upload your own CSV/Excel datasets and the dashboard rebuilds instantly with fresh insights.</div>
        </div>
        <div class="feature-card">
            <div class="fc-bar" style="background:linear-gradient(90deg,#6D28D9,#818CF8);"></div>
            <div class="feature-icon">&#128101;</div>
            <div class="feature-title">User Management</div>
            <div class="feature-desc">Admins can create, deactivate, promote, or remove users directly from within the dashboard.</div>
        </div>
    </div>
    """, height=340, scrolling=False)

    # ── Roles overview ────────────────────────────────────────────────
    components.html("""
    <style>
    * { font-family: Inter, sans-serif; box-sizing: border-box; margin: 0; padding: 0; }
    body { background: transparent; }
    .section-label {
        font-size: 10px; font-weight: 700; color: #4B5563;
        letter-spacing: 3px; text-transform: uppercase;
        text-align: center; margin-bottom: 16px;
    }
    .roles-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
    .role-chip {
        background: rgba(14,14,30,0.95);
        border-radius: 12px;
        border: 1px solid rgba(123,47,190,0.20);
        padding: 14px 10px;
        text-align: center;
    }
    .role-dot { width: 8px; height: 8px; border-radius: 50%; margin: 0 auto 8px auto; }
    .role-name { font-size: 11px; font-weight: 700; color: #D1D5DB; margin-bottom: 4px; }
    .role-perm { font-size: 10px; color: #4B5563; line-height: 1.4; }
    </style>
    <div class="section-label">Access Levels</div>
    <div class="roles-grid">
        <div class="role-chip">
            <div class="role-dot" style="background:#EF4444;"></div>
            <div class="role-name">Admin</div>
            <div class="role-perm">Full access + user management</div>
        </div>
        <div class="role-chip">
            <div class="role-dot" style="background:#F59E0B;"></div>
            <div class="role-name">Sales Manager</div>
            <div class="role-perm">Analytics, chat &amp; reports</div>
        </div>
        <div class="role-chip">
            <div class="role-dot" style="background:#38BDF8;"></div>
            <div class="role-name">Analyst</div>
            <div class="role-perm">Deep data &amp; downloads</div>
        </div>
        <div class="role-chip">
            <div class="role-dot" style="background:#C084FC;"></div>
            <div class="role-name">Executive</div>
            <div class="role-perm">KPIs &amp; PDF reports</div>
        </div>
        <div class="role-chip">
            <div class="role-dot" style="background:#6B7280;"></div>
            <div class="role-name">Viewer</div>
            <div class="role-perm">Read-only dashboard</div>
        </div>
    </div>
    """, height=130, scrolling=False)

    # ── Footer ────────────────────────────────────────────────────────
    st.markdown("""
    <div class="land-footer">
        <p>AI SALES ANALYTICS · TEAM 5 · POWERED BY GROQ &amp; STREAMLIT</p>
    </div>
    """, unsafe_allow_html=True)