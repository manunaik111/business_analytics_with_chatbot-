# auth/register_page.py
# Self-registration page — Viewer role only — Midnight Aurora theme

import streamlit as st
from .auth_manager import register_viewer
from .loading import show_inline_spinner, wrap_page_fade


def show_register_page():
    """Render the Viewer self-registration page."""

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
            radial-gradient(ellipse at 20% 20%, rgba(123,47,190,0.10) 0%, transparent 55%),
            radial-gradient(ellipse at 80% 80%, rgba(0,212,255,0.06) 0%, transparent 55%);
    }

    .block-container {
        max-width: 500px !important;
        padding-top: 3.5rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* ── Card ── */
    .reg-card {
        background: rgba(14, 14, 30, 0.88);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border-radius: 24px;
        border: 1px solid rgba(0,212,255,0.22);
        box-shadow:
            0 24px 64px rgba(0,0,0,0.55),
            0 0 40px rgba(0,212,255,0.08),
            inset 0 1px 0 rgba(255,255,255,0.04);
        padding: 36px 36px 24px 36px;
        margin-bottom: 0;
    }

    /* ── Title ── */
    .reg-title {
        background: linear-gradient(270deg, #00D4FF, #38BDF8, #C084FC, #00D4FF);
        background-size: 300% 300%;
        animation: gradientShift 5s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.65rem;
        font-weight: 900;
        text-align: center;
        letter-spacing: -0.5px;
        margin-bottom: 4px;
    }
    .reg-sub {
        color: #4B5563 !important;
        font-size: 11px;
        text-align: center;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-bottom: 0;
    }
    .reg-divider {
        height: 1px;
        background: linear-gradient(90deg,
            transparent, rgba(0,212,255,0.6), rgba(123,47,190,0.6), transparent);
        margin: 20px 0 18px 0;
        border: none;
    }

    @keyframes gradientShift {
        0%   { background-position: 0% 50%;   }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%;   }
    }

    /* ── Viewer badge ── */
    .viewer-badge {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        background: rgba(0,212,255,0.07);
        border: 1px solid rgba(0,212,255,0.20);
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 18px;
    }
    .viewer-badge-icon {
        font-size: 18px;
    }
    .viewer-badge-text {
        font-size: 12px;
        color: #6B7280 !important;
        line-height: 1.5;
    }
    .viewer-badge-text b {
        color: #38BDF8 !important;
    }

    /* ── Inputs ── */
    div[data-baseweb="input"] > div {
        background: rgba(18,18,40,0.9) !important;
        border: 1px solid rgba(0,212,255,0.22) !important;
        border-radius: 10px !important;
        color: #E0E0E0 !important;
    }
    div[data-baseweb="input"] > div:focus-within {
        border-color: #00D4FF !important;
        box-shadow: 0 0 0 3px rgba(0,212,255,0.12) !important;
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

    /* ── Password strength bar ── */
    .pw-strength-wrap {
        margin: -8px 0 10px 0;
    }
    .pw-strength-bar {
        height: 3px;
        border-radius: 3px;
        transition: width 0.3s ease, background 0.3s ease;
        margin-bottom: 4px;
    }
    .pw-strength-label {
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    /* ── Register button ── */
    div[data-testid="stButton"] { width: 100% !important; }
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #0369A1, #0891B2) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 14px 0 !important;
        width: 100% !important;
        min-height: 48px !important;
        box-shadow: 0 0 20px rgba(0,212,255,0.25) !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.5px !important;
        margin-top: 6px !important;
    }
    div[data-testid="stButton"] > button:hover {
        box-shadow: 0 0 32px rgba(0,212,255,0.45) !important;
        transform: translateY(-2px) !important;
    }

    /* ── Back to login link ── */
    .back-link {
        text-align: center;
        margin-top: 16px;
        font-size: 12px;
        color: #4B5563 !important;
    }
    .back-link b { color: #7B2FBE !important; cursor: pointer; }

    /* ── Alert ── */
    div[data-testid="stAlert"] {
        background: rgba(18,18,35,0.75) !important;
        border-radius: 10px !important;
        backdrop-filter: blur(10px) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Header card ──────────────────────────────────────────────────
    st.markdown("""
    <div class="reg-card">
        <div class="reg-title">Create Account</div>
        <div class="reg-sub">Viewer Access · Sales Analytics</div>
        <div class="reg-divider"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Viewer-only notice ────────────────────────────────────────────
    st.markdown("""
    <div class="viewer-badge">
        <span class="viewer-badge-icon">👁️</span>
        <div class="viewer-badge-text">
            Self-registered accounts are granted <b>Viewer</b> access only —
            read-only dashboard visibility. Contact an admin to upgrade your role.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Form fields ───────────────────────────────────────────────────
    full_name = st.text_input(
        "Full Name",
        placeholder="Jane Doe",
        key="reg_name"
    )

    email = st.text_input(
        "Email Address",
        placeholder="you@company.com",
        key="reg_email"
    )

    password = st.text_input(
        "Password",
        placeholder="Min 8 characters",
        type="password",
        key="reg_pw1"
    )

    # ── Live password strength indicator ─────────────────────────────
    if password:
        strength, color, label = _password_strength(password)
        width = ["25%", "50%", "75%", "100%"][strength - 1]
        st.markdown(f"""
        <div class="pw-strength-wrap">
            <div class="pw-strength-bar"
                 style="width:{width}; background:{color};"></div>
            <span class="pw-strength-label" style="color:{color};">{label}</span>
        </div>
        """, unsafe_allow_html=True)

    confirm_password = st.text_input(
        "Confirm Password",
        placeholder="Repeat your password",
        type="password",
        key="reg_pw2"
    )

    # ── Password match hint ───────────────────────────────────────────
    if confirm_password and password:
        if password == confirm_password:
            st.markdown(
                '<p style="color:#22C55E;font-size:11px;margin-top:-8px;">'
                '✓ Passwords match</p>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<p style="color:#EF4444;font-size:11px;margin-top:-8px;">'
                '✗ Passwords do not match</p>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Submit ────────────────────────────────────────────────────────
    if st.button("Create Viewer Account", key="reg_submit", type="primary"):
        error = _validate(full_name, email, password, confirm_password)
        if error:
            st.error(error)
        else:
            slot = show_inline_spinner("Creating your account…")
            ok, msg = register_viewer(full_name, email, password)
            slot.empty()
            if ok:
                st.success("🎉 Account created! You can now sign in.")
                st.session_state.current_page = "login"
                import time; time.sleep(1.2)
                st.rerun()
            else:
                st.error(msg)

    # ── Back to login ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Sign In", key="reg_back", type="secondary"):
        st.session_state.current_page = "login"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════

def _validate(name, email, pw, pw2) -> str | None:
    """Return an error string, or None if all valid."""
    if not all([name, email, pw, pw2]):
        return "All fields are required."
    if len(name.strip()) < 2:
        return "Please enter your full name."
    if "@" not in email or "." not in email.split("@")[-1]:
        return "Please enter a valid email address."
    if len(pw) < 8:
        return "Password must be at least 8 characters."
    if pw != pw2:
        return "Passwords do not match."
    return None


def _password_strength(pw: str) -> tuple[int, str, str]:
    """
    Return (score 1-4, hex color, label).
    Checks: length, uppercase, digits, special chars.
    """
    score = 0
    if len(pw) >= 8:                                      score += 1
    if len(pw) >= 12:                                     score += 1
    if any(c.isupper() for c in pw) and any(c.isdigit() for c in pw): score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in pw): score += 1

    score = max(1, min(score, 4))
    palette = {
        1: ("#EF4444", "Weak"),
        2: ("#F59E0B", "Fair"),
        3: ("#38BDF8", "Good"),
        4: ("#22C55E", "Strong"),
    }
    color, label = palette[score]
    return score, color, label