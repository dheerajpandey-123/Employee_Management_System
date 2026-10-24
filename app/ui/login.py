import streamlit as st
from textwrap import dedent

from app.database import SessionLocal
from app.services.auth_service import AuthService
_original_markdown = st.markdown


def _safe_markdown(body, *args, **kwargs):
    if isinstance(body, str):
        body = dedent(body).strip()

    _original_markdown(body, *args, **kwargs)


st.markdown = _safe_markdown


def render_login_page() -> None:
    # ============================================================
    # PREMIUM LOGIN EXPERIENCE
    # ============================================================
    from app.ui.theme import apply_theme
    current_theme = st.session_state.get("theme", "dark")
    apply_theme(current_theme)

    # Top theme switcher bar
    top_col1, top_col2 = st.columns([8, 2])
    with top_col2:
        is_dark = (current_theme == "dark")
        theme_toggle = st.toggle("🌙 Dark" if is_dark else "☀️ Light", value=is_dark, key="login_theme_toggle")
        new_theme = "dark" if theme_toggle else "light"
        if new_theme != current_theme:
            st.session_state["theme"] = new_theme
            st.rerun()

    st.html(
        """
        <style>

        /* ========================================================
           GLOBAL
           ======================================================== */

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(
                    900px 500px at 5% 0%,
                    rgba(99, 102, 241, 0.16),
                    transparent 65%
                ),
                radial-gradient(
                    700px 500px at 100% 100%,
                    rgba(14, 165, 233, 0.10),
                    transparent 65%
                ),
                #050812;
        }

        [data-testid="stHeader"] {
            background: transparent !important;
        }

        [data-testid="stToolbar"] {
            visibility: hidden;
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1240px;
            padding-top: 48px;
            padding-bottom: 48px;
        }

        [data-testid="stHorizontalBlock"] {
            align-items: stretch;
            gap: 18px;
        }


        /* ========================================================
           APPLICATION CARDS
           ======================================================== */

        [data-testid="stVerticalBlockBorderWrapper"] {
            min-height: 650px;

            border: 1px solid rgba(148, 163, 184, 0.14) !important;
            border-radius: 28px !important;

            background:
                linear-gradient(
                    145deg,
                    rgba(15, 23, 42, 0.96),
                    rgba(7, 12, 24, 0.98)
                ) !important;

            box-shadow:
                0 35px 90px rgba(0, 0, 0, 0.42),
                inset 0 1px 0 rgba(255, 255, 255, 0.035);

            overflow: hidden;
        }


        /* ========================================================
           LEFT BRAND CARD
           ======================================================== */

        [data-testid="stHorizontalBlock"]
        > div:first-child
        [data-testid="stVerticalBlockBorderWrapper"] {

            background:
                radial-gradient(
                    500px 300px at 10% 0%,
                    rgba(99, 102, 241, 0.20),
                    transparent 70%
                ),
                radial-gradient(
                    450px 300px at 100% 100%,
                    rgba(14, 165, 233, 0.10),
                    transparent 70%
                ),
                linear-gradient(
                    145deg,
                    #10172b,
                    #0b1120 60%,
                    #080d19
                ) !important;
        }


        /* ========================================================
           BRAND HEADER
           ======================================================== */

        .brand-topline {
            display: flex;
            align-items: center;
            gap: 12px;

            margin-bottom: 38px;
        }

        .brand-logo {
            width: 58px;
            height: 58px;

            display: flex;
            align-items: center;
            justify-content: center;

            border-radius: 17px;

            background:
                linear-gradient(
                    135deg,
                    #818cf8,
                    #4f46e5 65%,
                    #4338ca
                );

            color: #ffffff;

            font-size: 20px;
            font-weight: 850;
            letter-spacing: -1px;

            box-shadow:
                0 15px 35px rgba(79, 70, 229, 0.34);

            border: 1px solid rgba(255,255,255,0.10);
        }

        .brand-product {
            color: #e2e8f0;
            font-size: 13px;
            font-weight: 750;
            letter-spacing: 0.2px;
        }

        .brand-product-subtitle {
            margin-top: 3px;
            color: #64748b;
            font-size: 10px;
            letter-spacing: 0.7px;
            text-transform: uppercase;
        }


        /* ========================================================
           BRAND CONTENT
           ======================================================== */

        .brand-kicker {
            margin-bottom: 14px;

            color: #a5b4fc;
            font-size: 10px;
            font-weight: 800;

            letter-spacing: 2px;
            text-transform: uppercase;
        }

        .brand-title {
            margin-bottom: 22px;

            color: #f8fafc;
            font-size: 43px;
            font-weight: 850;

            line-height: 1.08;
            letter-spacing: -1.8px;
        }

        .brand-title-accent {
            color: #818cf8;
        }

        .brand-description {
            max-width: 560px;

            margin-bottom: 34px;

            color: #94a3b8;
            font-size: 14px;
            line-height: 1.8;
        }


        /* ========================================================
           FEATURE ROWS
           ======================================================== */

        .feature-list {
            display: flex;
            flex-direction: column;
            gap: 11px;
        }

        .feature-row {
            display: flex;
            align-items: center;
            gap: 12px;

            padding: 11px 13px;

            border: 1px solid rgba(148,163,184,0.08);
            border-radius: 13px;

            background: rgba(255,255,255,0.025);

            color: #cbd5e1;
            font-size: 12px;

            transition: 0.2s ease;
        }

        .feature-row:hover {
            border-color: rgba(129,140,248,0.22);
            background: rgba(99,102,241,0.06);
        }

        .feature-icon {
            width: 30px;
            height: 30px;
            flex-shrink: 0;

            display: inline-flex;
            align-items: center;
            justify-content: center;

            border: 1px solid rgba(129,140,248,0.20);
            border-radius: 9px;

            background: rgba(99,102,241,0.10);

            color: #a5b4fc;
            font-size: 12px;
            font-weight: 800;
        }


        /* ========================================================
           TRUST METRICS
           ======================================================== */

        .trust-strip {
            display: flex;
            gap: 28px;

            margin-top: 32px;
            padding-top: 25px;

            border-top: 1px solid rgba(148,163,184,0.09);
        }

        .trust-item {
            display: flex;
            flex-direction: column;
            gap: 3px;
        }

        .trust-value {
            color: #e2e8f0;
            font-size: 13px;
            font-weight: 750;
        }

        .trust-label {
            color: #64748b;
            font-size: 9px;
            letter-spacing: 0.8px;
            text-transform: uppercase;
        }


        /* ========================================================
           BRAND FOOTER
           ======================================================== */

        .brand-footer {
            margin-top: 58px;

            color: #475569;
            font-size: 10px;
        }


        /* ========================================================
           LOGIN HEADER
           ======================================================== */

        .security-badge {
            display: inline-flex;
            align-items: center;
            gap: 7px;

            margin-bottom: 25px;
            padding: 7px 11px;

            border: 1px solid rgba(34,197,94,0.18);
            border-radius: 999px;

            background: rgba(34,197,94,0.055);

            color: #86efac;
            font-size: 10px;
            font-weight: 750;
        }

        .security-dot {
            width: 6px;
            height: 6px;

            border-radius: 50%;

            background: #4ade80;

            box-shadow:
                0 0 10px rgba(74,222,128,0.75);
        }

        .login-title {
            margin-bottom: 8px;

            color: #f8fafc;
            font-size: 34px;
            font-weight: 850;

            letter-spacing: -1.1px;
        }

        .login-description {
            margin-bottom: 30px;

            color: #64748b;
            font-size: 13px;
            line-height: 1.65;
        }


        /* ========================================================
           FORM
           ======================================================== */

        div[data-testid="stForm"] {
            padding: 0 !important;
            border: none !important;
            background: transparent !important;
        }

        div[data-testid="stTextInput"] {
            margin-bottom: 5px;
        }

        div[data-testid="stTextInput"] label {
            color: #cbd5e1 !important;

            font-size: 12px !important;
            font-weight: 700 !important;
        }

        div[data-testid="stTextInput"] input {
            min-height: 50px !important;

            border: 1px solid #273449 !important;
            border-radius: 12px !important;

            background:
                rgba(15,23,42,0.92) !important;

            color: #f8fafc !important;

            transition:
                border-color 0.2s ease,
                box-shadow 0.2s ease;
        }

        div[data-testid="stTextInput"] input:hover {
            border-color: #3b4a63 !important;
        }

        div[data-testid="stTextInput"] input:focus {
            border-color: #6366f1 !important;

            box-shadow:
                0 0 0 3px rgba(99,102,241,0.11),
                0 8px 25px rgba(0,0,0,0.12) !important;
        }

        div[data-testid="stFormSubmitButton"] button {
            min-height: 51px !important;

            margin-top: 14px;

            border: 1px solid rgba(129,140,248,0.35) !important;
            border-radius: 12px !important;

            background:
                linear-gradient(
                    135deg,
                    #6366f1,
                    #4f46e5
                ) !important;

            color: #ffffff !important;

            font-size: 13px !important;
            font-weight: 750 !important;

            box-shadow:
                0 14px 30px rgba(79,70,229,0.24);
        }

        div[data-testid="stFormSubmitButton"] button:hover {
            background:
                linear-gradient(
                    135deg,
                    #818cf8,
                    #4f46e5
                ) !important;

            box-shadow:
                0 18px 38px rgba(79,70,229,0.34);
        }


        /* ========================================================
           LOGIN TRUST AREA
           ======================================================== */

        .login-trust {
            display: flex;
            align-items: center;
            gap: 9px;

            margin-top: 24px;
            padding: 12px 13px;

            border: 1px solid rgba(148,163,184,0.08);
            border-radius: 12px;

            background: rgba(255,255,255,0.025);

            color: #64748b;
            font-size: 10px;
            line-height: 1.5;
        }

        .login-trust-icon {
            color: #86efac;
            font-size: 14px;
        }


        /* ========================================================
           LOGIN FOOTER
           ======================================================== */

        .login-footer {
            margin-top: 25px;
            padding-top: 20px;

            border-top: 1px solid rgba(148,163,184,0.08);

            color: #475569;
            font-size: 10px;
            line-height: 1.7;

            text-align: center;
        }


        /* ========================================================
           RESPONSIVE
           ======================================================== */

        @media (max-width: 900px) {

            [data-testid="stMainBlockContainer"] {
                padding: 25px;
            }

            [data-testid="stVerticalBlockBorderWrapper"] {
                min-height: auto;
            }

            .brand-title {
                font-size: 36px;
            }

            .brand-footer {
                margin-top: 40px;
            }
        }


        @media (max-width: 520px) {

            [data-testid="stMainBlockContainer"] {
                padding: 14px;
            }

            .brand-title {
                font-size: 30px;
            }

            .login-title {
                font-size: 28px;
            }

            .trust-strip {
                gap: 18px;
            }
        }

        </style>
        """,

    )


    # ============================================================
    # MAIN LAYOUT
    # ============================================================

    left_column, right_column = st.columns(
        [1.08, 0.92],
        gap="small",
    )


    # ============================================================
    # LEFT — PRODUCT / BRAND
    # ============================================================

    with left_column:

        with st.container(border=True):

            st.html(
                """
                <div class="brand-topline">

                    <div class="brand-logo">
                        EM
                    </div>

                    <div>
                        <div class="brand-product">
                            Employee Management System
                        </div>

                        <div class="brand-product-subtitle">
                            Workforce Operations Platform
                        </div>
                    </div>

                </div>
                """,

            )

            st.html(
                """
                <div class="brand-kicker">
                    WORKFORCE INTELLIGENCE PLATFORM
                </div>

                <div class="brand-title">
                    Manage your workforce
                    <span class="brand-title-accent">
                        with confidence.
                    </span>
                </div>

                <div class="brand-description">
                    A centralized workforce platform built for
                    secure employee operations, faster decisions,
                    reliable information, and measurable
                    organizational performance.
                </div>
                """,

            )

            st.html(
                """
                <div class="feature-list">

                    <div class="feature-row">
                        <span class="feature-icon">✓</span>
                        <span>
                            Secure role-based workforce access
                        </span>
                    </div>

                    <div class="feature-row">
                        <span class="feature-icon">⌁</span>
                        <span>
                            Performance-focused employee operations
                        </span>
                    </div>

                    <div class="feature-row">
                        <span class="feature-icon">▣</span>
                        <span>
                            Centralized workforce information
                        </span>
                    </div>

                </div>
                """,

            )

            st.html(
                """
                <div class="trust-strip">

                    <div class="trust-item">
                        <div class="trust-value">
                            Role Based
                        </div>
                        <div class="trust-label">
                            Access Control
                        </div>
                    </div>

                    <div class="trust-item">
                        <div class="trust-value">
                            Secure
                        </div>
                        <div class="trust-label">
                            Authentication
                        </div>
                    </div>

                    <div class="trust-item">
                        <div class="trust-value">
                            Performance
                        </div>
                        <div class="trust-label">
                            Focused
                        </div>
                    </div>

                </div>
                """,

            )

            st.html(
                """
                <div class="brand-footer">
                    Employee Management System
                    &nbsp;·&nbsp;
                    Secure Workforce Portal
                </div>
                """,

            )


    # ============================================================
    # RIGHT — AUTHENTICATION
    # ============================================================

    with right_column:

        with st.container(border=True):

            st.html(
                """
                <div class="security-badge">
                    <span class="security-dot"></span>
                    Secure authentication enabled
                </div>
                """,

            )

            st.html(
                '<div class="login-title">Welcome back</div>',

            )

            st.html(
                """
                <div class="login-description">
                    Sign in with your authorized workforce
                    account to continue to your workspace.
                </div>
                """,

            )


            # ----------------------------------------------------
            # REAL STREAMLIT AUTH FORM
            # ----------------------------------------------------

            with st.form("login_form"):

                username = st.text_input(
                    "Username or Email",
                    placeholder="Enter username (e.g. admin123, admin) or email",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                )

                submitted = st.form_submit_button(
                    "Sign In",
                    type="primary",
                    width="stretch",
                )


            # ----------------------------------------------------
            # AUTHENTICATION
            # ----------------------------------------------------

            if submitted:

                db = SessionLocal()

                try:

                    try:
                        user = AuthService(db).authenticate(
                            username=username,
                            password=password,
                        )

                    except ValueError:
                        user = None


                    if user is None:

                        st.error(
                            "Invalid username or password. Check credentials or use 1-Click Demo Login below."
                        )

                    else:

                        st.session_state["authenticated"] = True
                        st.session_state["user_id"] = user.id
                        st.session_state["username"] = user.username
                        st.session_state["role"] = user.role

                        st.success(
                            "Authentication successful."
                        )

                        st.rerun()

                finally:
                    db.close()

            # ----------------------------------------------------
            # DEMO CREDENTIALS SHORTCUT & 1-CLICK QUICK LOGIN
            # ----------------------------------------------------
            with st.expander("🔑 Demo Accounts & 1-Click Login", expanded=True):
                st.markdown(
                    """
                    <div class="login-demo-accounts" style="font-size:12px; line-height:1.7; margin-bottom:10px;">
                    🛡️ <strong>Admin:</strong> <code>admin123</code> / <code>Admin@123</code> (or <code>admin</code>)<br>
                    👥 <strong>HR Manager:</strong> <code>hr_manager</code> / <code>Hr@123456</code><br>
                    👤 <strong>Employee:</strong> <code>emp001</code> / <code>Employee@123</code>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                q1, q2, q3 = st.columns(3)
                with q1:
                    if st.button("🛡️ Admin", key="quick_admin_btn", width="stretch"):
                        db = SessionLocal()
                        try:
                            user = AuthService(db).authenticate("admin123", "Admin@123")
                            if user:
                                st.session_state["authenticated"] = True
                                st.session_state["user_id"] = user.id
                                st.session_state["username"] = user.username
                                st.session_state["role"] = user.role
                                st.rerun()
                        finally:
                            db.close()

                with q2:
                    if st.button("👥 HR", key="quick_hr_btn", width="stretch"):
                        db = SessionLocal()
                        try:
                            user = AuthService(db).authenticate("hr_manager", "Hr@123456")
                            if user:
                                st.session_state["authenticated"] = True
                                st.session_state["user_id"] = user.id
                                st.session_state["username"] = user.username
                                st.session_state["role"] = user.role
                                st.rerun()
                        finally:
                            db.close()

                with q3:
                    if st.button("👤 Employee", key="quick_emp_btn", width="stretch"):
                        db = SessionLocal()
                        try:
                            user = AuthService(db).authenticate("emp001", "Employee@123")
                            if user:
                                st.session_state["authenticated"] = True
                                st.session_state["user_id"] = user.id
                                st.session_state["username"] = user.username
                                st.session_state["role"] = user.role
                                st.rerun()
                        finally:
                            db.close()


            # ----------------------------------------------------
            # SECURITY INFORMATION
            # ----------------------------------------------------

            st.html(
                """
                <div class="login-trust">

                    <span class="login-trust-icon">
                        🔒
                    </span>

                    <span>
                        Your credentials are protected using
                        secure password hashing and
                        role-based authentication.
                    </span>

                </div>
                """,

            )

            st.html(
                """
                <div class="login-footer">
                    Authorized workforce accounts only.<br>
                    Employee Management System
                </div>
                """,

            )


if __name__ == "__main__":
    render_login_page()


