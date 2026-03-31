# auth/auth_manager.py
# Authentication manager — SQLite + bcrypt + session management

import sqlite3
import bcrypt
import os
import streamlit as st
from datetime import datetime
from .roles import ALL_ROLES, ROLE_ADMIN, has_permission, get_permissions

# ── DB Path ───────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

SESSION_TIMEOUT_MINUTES = 30


# ══════════════════════════════════════════════════════════════════════
# Database Setup
# ══════════════════════════════════════════════════════════════════════
def init_db():
    """Create users table if it doesn't exist and seed default admin."""
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL,
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_at    TEXT    NOT NULL,
            last_login    TEXT
        )
    """)
    conn.commit()

    # Seed default Admin if no users exist
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        _create_user_internal(
            conn,
            full_name = "System Admin",
            email     = "admin@sales.com",
            password  = "Admin@1234",
            role      = ROLE_ADMIN
        )

    conn.close()


def _create_user_internal(conn, full_name, email, password, role):
    """Internal helper — inserts a user directly using an open connection."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn.cursor().execute(
        """INSERT INTO users (full_name, email, password_hash, role, is_active, created_at)
           VALUES (?, ?, ?, ?, 1, ?)""",
        (full_name, email, hashed, role, datetime.now().isoformat())
    )
    conn.commit()


# ══════════════════════════════════════════════════════════════════════
# User CRUD
# ══════════════════════════════════════════════════════════════════════
def create_user(full_name: str, email: str, password: str, role: str) -> tuple[bool, str]:
    """Create a new user. Returns (success, message)."""
    if role not in ALL_ROLES:
        return False, f"Invalid role '{role}'"
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if '@' not in email:
        return False, "Invalid email address"

    try:
        conn   = sqlite3.connect(DB_PATH)
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn.cursor().execute(
            """INSERT INTO users (full_name, email, password_hash, role, is_active, created_at)
               VALUES (?, ?, ?, ?, 1, ?)""",
            (full_name, email.lower().strip(), hashed, role, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return True, f"User '{full_name}' created successfully"
    except sqlite3.IntegrityError:
        return False, "Email already exists"
    except Exception as e:
        return False, str(e)


def get_all_users() -> list[dict]:
    """Return all users as a list of dicts (no password hashes)."""
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT id, full_name, email, role, is_active, created_at, last_login FROM users ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "full_name": r[1], "email": r[2],
            "role": r[3], "is_active": bool(r[4]),
            "created_at": r[5], "last_login": r[6]
        }
        for r in rows
    ]


def update_user_role(user_id: int, new_role: str) -> tuple[bool, str]:
    """Update a user's role."""
    if new_role not in ALL_ROLES:
        return False, "Invalid role"
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.cursor().execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        conn.commit()
        conn.close()
        return True, "Role updated successfully"
    except Exception as e:
        return False, str(e)


def toggle_user_active(user_id: int) -> tuple[bool, str]:
    """Enable or disable a user account."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c    = conn.cursor()
        c.execute("SELECT is_active, email FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        if not row:
            return False, "User not found"
        new_status = 0 if row[0] else 1
        c.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
        conn.commit()
        conn.close()
        status_text = "activated" if new_status else "deactivated"
        return True, f"User {status_text} successfully"
    except Exception as e:
        return False, str(e)


def delete_user(user_id: int) -> tuple[bool, str]:
    """Delete a user by ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.cursor().execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True, "User deleted successfully"
    except Exception as e:
        return False, str(e)


def reset_password(user_id: int, new_password: str) -> tuple[bool, str]:
    """Reset a user's password."""
    if len(new_password) < 8:
        return False, "Password must be at least 8 characters"
    try:
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn   = sqlite3.connect(DB_PATH)
        conn.cursor().execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed, user_id))
        conn.commit()
        conn.close()
        return True, "Password reset successfully"
    except Exception as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════════
# Authentication
# ══════════════════════════════════════════════════════════════════════
def verify_login(email: str, password: str) -> tuple[bool, dict | str]:
    """
    Verify credentials.
    Returns (True, user_dict) on success or (False, error_message) on failure.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c    = conn.cursor()
        c.execute(
            "SELECT id, full_name, email, password_hash, role, is_active FROM users WHERE email = ?",
            (email.lower().strip(),)
        )
        row = c.fetchone()
        conn.close()

        if not row:
            return False, "Invalid email or password"
        if not row[5]:
            return False, "Your account has been deactivated. Contact admin."
        if not bcrypt.checkpw(password.encode('utf-8'), row[3].encode('utf-8')):
            return False, "Invalid email or password"

        # Update last_login
        conn = sqlite3.connect(DB_PATH)
        conn.cursor().execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(), row[0])
        )
        conn.commit()
        conn.close()

        user = {
            "id":          row[0],
            "full_name":   row[1],
            "email":       row[2],
            "role":        row[4],
            "permissions": get_permissions(row[4]),
            "login_time":  datetime.now().isoformat()
        }
        return True, user

    except Exception as e:
        return False, f"Login error: {str(e)}"


# ══════════════════════════════════════════════════════════════════════
# Session Management
# ══════════════════════════════════════════════════════════════════════
def init_session():
    """Initialize auth-related session state keys."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user'  not in st.session_state:
        st.session_state.current_user  = None
    if 'login_time'    not in st.session_state:
        st.session_state.login_time    = None


def login_user(user: dict):
    """Store authenticated user in session."""
    st.session_state.authenticated = True
    st.session_state.current_user  = user
    st.session_state.login_time    = datetime.now()


def logout_user():
    """Clear session state."""
    st.session_state.authenticated = False
    st.session_state.current_user  = None
    st.session_state.login_time    = None
    # Clear chat state too
    for key in ['chat_open', 'chat_messages', 'conversation_history', 'pending_q']:
        if key in st.session_state:
            del st.session_state[key]


def is_authenticated() -> bool:
    """Check if user is logged in and session hasn't timed out."""
    if not st.session_state.get('authenticated', False):
        return False
    login_time = st.session_state.get('login_time')
    if login_time:
        elapsed = (datetime.now() - login_time).total_seconds() / 60
        if elapsed > SESSION_TIMEOUT_MINUTES:
            logout_user()
            return False
    return True


def current_user() -> dict | None:
    """Return current logged-in user dict."""
    return st.session_state.get('current_user')


def can(permission: str) -> bool:
    """Check if current user has a specific permission."""
    user = current_user()
    if not user:
        return False
    return has_permission(user['role'], permission)