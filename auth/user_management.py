# auth/user_management.py
# Admin-only user management panel — Midnight Aurora theme

import streamlit as st
import pandas as pd
from .auth_manager import (
    get_all_users, create_user, update_user_role,
    toggle_user_active, delete_user, reset_password, current_user
)
from .roles import ALL_ROLES, ROLE_COLORS, ROLE_DESCRIPTIONS


def show_user_management():
    """Render the full user management panel (Admin only)."""

    st.markdown("""
    <style>
    .um-section {
        background: rgba(12,12,28,0.80);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        border: 1px solid rgba(123,47,190,0.22);
        padding: 20px 22px;
        margin-bottom: 18px;
    }
    .um-title {
        font-size: 10px !important;
        font-weight: 700 !important;
        color: #4B5563 !important;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .um-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(123,47,190,0.5), transparent);
    }
    .role-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        border: 1px solid;
    }
    .user-row {
        background: rgba(18,18,40,0.6);
        border-radius: 10px;
        border: 1px solid rgba(123,47,190,0.15);
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="um-title">User Management</div>', unsafe_allow_html=True)

    me = current_user()

    # ── Tabs ──────────────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["All Users", "Add New User"])

    # ── Tab 1: All Users ──────────────────────────────────────────────
    with tab1:
        users = get_all_users()
        if not users:
            st.info("No users found.")
        else:
            for u in users:
                is_me    = u['email'] == me['email']
                color    = ROLE_COLORS.get(u['role'], '#6B7280')
                status   = "🟢 Active" if u['is_active'] else "🔴 Inactive"
                login_ts = u['last_login'][:10] if u['last_login'] else "Never"

                with st.expander(
                    f"{'🔒 ' if is_me else ''}{u['full_name']}  •  {u['email']}  •  {u['role']}",
                    expanded=False
                ):
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Status:** {status}")
                    c2.markdown(f"**Last Login:** {login_ts}")
                    c3.markdown(f"**Created:** {u['created_at'][:10]}")

                    st.markdown("---")

                    if is_me:
                        st.caption("⚠️ You cannot modify your own account here.")
                    else:
                        a1, a2, a3, a4 = st.columns(4)

                        # Change role
                        with a1:
                            new_role = st.selectbox(
                                "Change Role",
                                ALL_ROLES,
                                index=ALL_ROLES.index(u['role']),
                                key=f"role_{u['id']}"
                            )
                            if st.button("Update Role", key=f"upd_{u['id']}"):
                                ok, msg = update_user_role(u['id'], new_role)
                                st.success(msg) if ok else st.error(msg)
                                st.rerun()

                        # Reset password
                        with a2:
                            new_pw = st.text_input(
                                "New Password", type="password",
                                key=f"pw_{u['id']}", placeholder="Min 8 chars"
                            )
                            if st.button("Reset Password", key=f"rpw_{u['id']}"):
                                if new_pw:
                                    ok, msg = reset_password(u['id'], new_pw)
                                    st.success(msg) if ok else st.error(msg)
                                else:
                                    st.warning("Enter a new password first.")

                        # Toggle active
                        with a3:
                            st.markdown("<br>", unsafe_allow_html=True)
                            btn_label = "Deactivate" if u['is_active'] else "Activate"
                            if st.button(btn_label, key=f"tog_{u['id']}"):
                                ok, msg = toggle_user_active(u['id'])
                                st.success(msg) if ok else st.error(msg)
                                st.rerun()

                        # Delete
                        with a4:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("Delete", key=f"del_{u['id']}",
                                         type="secondary"):
                                ok, msg = delete_user(u['id'])
                                st.success(msg) if ok else st.error(msg)
                                st.rerun()

    # ── Tab 2: Add New User ───────────────────────────────────────────
    with tab2:
        st.markdown('<div class="um-section">', unsafe_allow_html=True)
        st.markdown("#### Create New User")

        n1, n2 = st.columns(2)
        with n1:
            new_name  = st.text_input("Full Name",      key="nu_name",  placeholder="John Doe")
            new_email = st.text_input("Email Address",  key="nu_email", placeholder="john@company.com")
        with n2:
            new_pw1   = st.text_input("Password",       key="nu_pw1",   type="password", placeholder="Min 8 chars")
            new_pw2   = st.text_input("Confirm Password", key="nu_pw2", type="password", placeholder="Repeat password")

        new_role = st.selectbox("Assign Role", ALL_ROLES, key="nu_role")
        st.caption(f"ℹ️ {ROLE_DESCRIPTIONS.get(new_role, '')}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Create User", key="create_user_btn", type="primary"):
            if not all([new_name, new_email, new_pw1, new_pw2]):
                st.error("All fields are required.")
            elif new_pw1 != new_pw2:
                st.error("Passwords do not match.")
            else:
                ok, msg = create_user(new_name, new_email, new_pw1, new_role)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown('</div>', unsafe_allow_html=True)