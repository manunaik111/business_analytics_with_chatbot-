# auth/roles.py
# Role definitions and permission matrix for RBAC system

# ── Role Constants ────────────────────────────────────────────────────
ROLE_ADMIN         = "Admin"
ROLE_SALES_MANAGER = "Sales Manager"
ROLE_ANALYST       = "Analyst"
ROLE_EXECUTIVE     = "Executive"
ROLE_VIEWER        = "Viewer"

ALL_ROLES = [ROLE_ADMIN, ROLE_SALES_MANAGER, ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_VIEWER]

# ── Permission Constants ──────────────────────────────────────────────
PERM_VIEW_DASHBOARD      = "view_dashboard"       # View KPI cards and charts
PERM_VIEW_RAW_DATA       = "view_raw_data"         # View detailed data table
PERM_USE_CHATBOT         = "use_chatbot"           # Access AI chat assistant
PERM_DOWNLOAD_EXCEL      = "download_excel"        # Download Excel reports
PERM_DOWNLOAD_PDF        = "download_pdf"          # Download PDF reports
PERM_UPLOAD_DATA         = "upload_data"           # Upload new datasets
PERM_MANAGE_USERS        = "manage_users"          # Add/edit/delete users
PERM_VIEW_AI_INSIGHTS    = "view_ai_insights"      # View AI-powered insight cards
PERM_VIEW_ALL_CHARTS     = "view_all_charts"       # View all chart sections

# ── Permission Matrix ─────────────────────────────────────────────────
ROLE_PERMISSIONS = {
    ROLE_ADMIN: [
        PERM_VIEW_DASHBOARD,
        PERM_VIEW_RAW_DATA,
        PERM_USE_CHATBOT,
        PERM_DOWNLOAD_EXCEL,
        PERM_DOWNLOAD_PDF,
        PERM_UPLOAD_DATA,
        PERM_MANAGE_USERS,
        PERM_VIEW_AI_INSIGHTS,
        PERM_VIEW_ALL_CHARTS,
    ],
    ROLE_SALES_MANAGER: [
        PERM_VIEW_DASHBOARD,
        PERM_VIEW_RAW_DATA,
        PERM_USE_CHATBOT,
        PERM_DOWNLOAD_EXCEL,
        PERM_DOWNLOAD_PDF,
        PERM_VIEW_AI_INSIGHTS,
        PERM_VIEW_ALL_CHARTS,
    ],
    ROLE_ANALYST: [
        PERM_VIEW_DASHBOARD,
        PERM_VIEW_RAW_DATA,
        PERM_USE_CHATBOT,
        PERM_DOWNLOAD_EXCEL,
        PERM_DOWNLOAD_PDF,
        PERM_VIEW_AI_INSIGHTS,
        PERM_VIEW_ALL_CHARTS,
    ],
    ROLE_EXECUTIVE: [
        PERM_VIEW_DASHBOARD,
        PERM_DOWNLOAD_PDF,
        PERM_VIEW_AI_INSIGHTS,
    ],
    ROLE_VIEWER: [
        PERM_VIEW_DASHBOARD,
    ],
}

# ── Role Descriptions (for UI display) ───────────────────────────────
ROLE_DESCRIPTIONS = {
    ROLE_ADMIN:         "Full system access including user management and data upload",
    ROLE_SALES_MANAGER: "Full analytics access with chat and report downloads",
    ROLE_ANALYST:       "Deep data exploration, chat, and report downloads",
    ROLE_EXECUTIVE:     "KPI summary and PDF report downloads only",
    ROLE_VIEWER:        "Read-only dashboard access",
}

# ── Role Badge Colors (matches Midnight Aurora theme) ─────────────────
ROLE_COLORS = {
    ROLE_ADMIN:         "#EF4444",   # Red   — highest authority
    ROLE_SALES_MANAGER: "#F59E0B",   # Amber
    ROLE_ANALYST:       "#38BDF8",   # Cyan
    ROLE_EXECUTIVE:     "#C084FC",   # Purple
    ROLE_VIEWER:        "#6B7280",   # Grey  — lowest authority
}


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, [])


def get_permissions(role: str) -> list:
    """Return list of permissions for a role."""
    return ROLE_PERMISSIONS.get(role, [])