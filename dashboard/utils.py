"""utils.py — Shared utilities for Genesis AI / Zero Click AI Platform"""
import plotly.graph_objects as go

COLORS = ["#a78bfa", "#38bdf8", "#4ade80", "#fb923c", "#f472b6", "#fbbf24", "#818cf8", "#2dd4bf"]

def apply_genesis_theme(fig):
    """Apply the glassmorphism dark theme to any Plotly figure."""
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="rgba(255,255,255,0.75)", size=11),
        title_font=dict(size=13, color="rgba(255,255,255,0.85)", family="Inter, sans-serif"),
        margin=dict(l=0, r=0, t=36, b=0),
        xaxis=dict(showgrid=False, zeroline=False,
                   color="rgba(255,255,255,0.3)",
                   tickfont=dict(size=10, color="rgba(255,255,255,0.4)")),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False,
                   color="rgba(255,255,255,0.3)",
                   tickfont=dict(size=10, color="rgba(255,255,255,0.4)")),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color="rgba(255,255,255,0.55)")),
        coloraxis=dict(colorbar=dict(tickfont=dict(color="rgba(255,255,255,0.5)"))),
    )
    return fig

def format_number(num):
    """Format large numbers to readable strings (1M, 5K, etc.)."""
    try:
        num = float(num)
        if abs(num) >= 1_000_000_000:
            return f"{num / 1_000_000_000:.2f}B"
        elif abs(num) >= 1_000_000:
            return f"{num / 1_000_000:.2f}M"
        elif abs(num) >= 1_000:
            return f"{num / 1_000:.1f}K"
        elif isinstance(num, float) and not num.is_integer():
            return f"{num:.2f}"
        else:
            return str(int(num))
    except (ValueError, TypeError):
        return str(num)

def hex_to_rgb(h):
    h = h.lstrip("#")
    return ",".join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))
