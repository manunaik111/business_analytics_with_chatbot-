# auth/loading.py
# Reusable loading animations — Midnight Aurora theme

import streamlit as st
import time


# ══════════════════════════════════════════════════════════════════════
# CSS — injected once per session
# ══════════════════════════════════════════════════════════════════════
_LOADING_CSS = """
<style>
/* ── Spinner ── */
@keyframes aurora-spin {
    0%   { transform: rotate(0deg);   }
    100% { transform: rotate(360deg); }
}
@keyframes aurora-pulse {
    0%, 100% { opacity: 0.6; transform: scale(1);    }
    50%       { opacity: 1.0; transform: scale(1.08); }
}
@keyframes shimmer {
    0%   { background-position: -700px 0; }
    100% { background-position:  700px 0; }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0);    }
}
@keyframes dotBounce {
    0%, 80%, 100% { transform: translateY(0);    opacity: 0.4; }
    40%           { transform: translateY(-8px); opacity: 1.0; }
}

/* ── Full-screen overlay spinner ── */
.aurora-loader-overlay {
    position: fixed;
    inset: 0;
    background: rgba(8, 11, 20, 0.82);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    animation: fadeInUp 0.3s ease;
}
.aurora-spinner {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    border: 3px solid rgba(123, 47, 190, 0.18);
    border-top-color: #7B2FBE;
    border-right-color: #00D4FF;
    animation: aurora-spin 0.85s linear infinite;
    box-shadow: 0 0 22px rgba(123,47,190,0.40), 0 0 44px rgba(0,212,255,0.15);
}
.aurora-spinner-sm {
    width: 32px;
    height: 32px;
    border-width: 2px;
}
.aurora-loader-text {
    margin-top: 20px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    background: linear-gradient(90deg, #7B2FBE, #00D4FF, #C084FC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: aurora-pulse 1.8s ease-in-out infinite;
}

/* ── Dot loader (inline) ── */
.dot-loader {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 0;
}
.dot-loader span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7B2FBE, #00D4FF);
    animation: dotBounce 1.2s ease-in-out infinite;
    display: inline-block;
}
.dot-loader span:nth-child(2) { animation-delay: 0.15s; }
.dot-loader span:nth-child(3) { animation-delay: 0.30s; }

/* ── Skeleton cards ── */
.skeleton-base {
    background: linear-gradient(
        90deg,
        rgba(18,18,40,0.80) 25%,
        rgba(123,47,190,0.12) 50%,
        rgba(18,18,40,0.80) 75%
    );
    background-size: 700px 100%;
    animation: shimmer 1.6s infinite linear;
    border-radius: 10px;
}
.skeleton-kpi {
    height: 110px;
    border-radius: 18px;
    border: 1px solid rgba(123,47,190,0.18);
    margin-bottom: 0;
}
.skeleton-chart {
    border-radius: 18px;
    border: 1px solid rgba(123,47,190,0.18);
}
.skeleton-line {
    height: 14px;
    border-radius: 6px;
    margin-bottom: 10px;
}
.skeleton-line.short  { width: 55%; }
.skeleton-line.medium { width: 75%; }
.skeleton-line.full   { width: 100%; }

/* ── Progress bar ── */
.aurora-progress-wrap {
    width: 100%;
    height: 4px;
    background: rgba(123,47,190,0.15);
    border-radius: 4px;
    overflow: hidden;
    margin: 8px 0 16px 0;
}
.aurora-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #7B2FBE, #00D4FF, #C084FC);
    background-size: 200% 100%;
    border-radius: 4px;
    animation: shimmer 1.4s infinite linear;
}

/* ── Page transition fade ── */
.page-fade-in {
    animation: fadeInUp 0.45s ease both;
}
</style>
"""


def _inject_css():
    """Inject loading CSS once."""
    st.markdown(_LOADING_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════

def show_page_loader(message: str = "Loading"):
    """
    Full-screen overlay spinner with animated text.
    Use with st.empty():

        placeholder = st.empty()
        with placeholder:
            show_page_loader("Initialising…")
        time.sleep(1)
        placeholder.empty()
    """
    _inject_css()
    st.markdown(f"""
    <div class="aurora-loader-overlay">
        <div class="aurora-spinner"></div>
        <div class="aurora-loader-text">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def show_inline_spinner(message: str = "Processing…"):
    """
    Small inline spinner row. Returns the st.empty container so caller
    can clear it.

    Usage:
        slot = show_inline_spinner("Fetching data…")
        do_work()
        slot.empty()
    """
    _inject_css()
    slot = st.empty()
    slot.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;padding:12px 0;">
        <div class="aurora-spinner aurora-spinner-sm"></div>
        <span style="color:#9CA3AF;font-size:13px;font-weight:500;">{message}</span>
    </div>
    """, unsafe_allow_html=True)
    return slot


def show_dot_loader(message: str = ""):
    """Bouncing dot loader (compact, inline)."""
    _inject_css()
    slot = st.empty()
    label = f'<span style="color:#6B7280;font-size:12px;margin-left:8px;">{message}</span>' if message else ""
    slot.markdown(f"""
    <div style="display:flex;align-items:center;gap:0;">
        <div class="dot-loader">
            <span></span><span></span><span></span>
        </div>
        {label}
    </div>
    """, unsafe_allow_html=True)
    return slot


def show_skeleton_kpi(n_cards: int = 4):
    """Render n shimmer KPI card placeholders in a row."""
    _inject_css()
    cols = st.columns(n_cards)
    for col in cols:
        with col:
            st.markdown('<div class="skeleton-base skeleton-kpi"></div>',
                        unsafe_allow_html=True)


def show_skeleton_chart(height_px: int = 320):
    """Render a shimmer chart placeholder."""
    _inject_css()
    st.markdown(
        f'<div class="skeleton-base skeleton-chart" style="height:{height_px}px;"></div>',
        unsafe_allow_html=True
    )


def show_skeleton_text(lines: int = 3):
    """Render shimmer text-line placeholders."""
    _inject_css()
    sizes = ["full", "medium", "short"]
    html  = ""
    for i in range(lines):
        cls = sizes[i % len(sizes)]
        html += f'<div class="skeleton-base skeleton-line {cls}"></div>'
    st.markdown(html, unsafe_allow_html=True)


def show_progress_bar():
    """Thin animated aurora progress bar (indeterminate)."""
    _inject_css()
    st.markdown("""
    <div class="aurora-progress-wrap">
        <div class="aurora-progress-bar" style="width:100%;"></div>
    </div>
    """, unsafe_allow_html=True)


def loading_section(message: str = "Loading", height_px: int = 320,
                    show_kpi: bool = False, n_kpi: int = 4):
    """
    Convenience: shows skeletons while a section loads.
    Wrap your heavy computation like so:

        with st.spinner(''):          # hides default spinner
            loading_section(show_kpi=True)
            df = load_data()          # heavy call
        render_charts(df)
    """
    _inject_css()
    show_progress_bar()
    if show_kpi:
        show_skeleton_kpi(n_kpi)
        st.markdown("<br>", unsafe_allow_html=True)
    show_skeleton_chart(height_px)


def timed_loader(placeholder, message: str = "Loading", seconds: float = 1.2):
    """
    Show a page loader inside `placeholder` for `seconds`, then clear it.
    Useful for page transitions.

        ph = st.empty()
        timed_loader(ph, "Opening Dashboard…", seconds=1.0)
    """
    _inject_css()
    with placeholder:
        show_page_loader(message)
    time.sleep(seconds)
    placeholder.empty()


def wrap_page_fade():
    """Inject a CSS class that fades the whole page in on load."""
    _inject_css()
    st.markdown("""
    <style>
    .block-container { animation: fadeInUp 0.5s ease both; }
    </style>
    """, unsafe_allow_html=True)