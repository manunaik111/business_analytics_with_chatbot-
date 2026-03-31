# auth/__init__.py
from .auth_manager import (
    init_db, init_session, login_user, logout_user,
    is_authenticated, current_user, can,
    create_user, get_all_users, update_user_role,
    toggle_user_active, delete_user, reset_password
)
from .roles import (
    has_permission, get_permissions,
    ROLE_ADMIN, ROLE_SALES_MANAGER, ROLE_ANALYST,
    ROLE_EXECUTIVE, ROLE_VIEWER,
    PERM_VIEW_DASHBOARD, PERM_VIEW_RAW_DATA, PERM_USE_CHATBOT,
    PERM_DOWNLOAD_EXCEL, PERM_DOWNLOAD_PDF, PERM_UPLOAD_DATA,
    PERM_MANAGE_USERS, PERM_VIEW_AI_INSIGHTS, PERM_VIEW_ALL_CHARTS,
    ROLE_COLORS, ROLE_DESCRIPTIONS
)
from .login_page import show_login_page
from .user_management import show_user_management