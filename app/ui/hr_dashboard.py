from __future__ import annotations

from datetime import date
from html import escape
import logging

import pandas as pd
import plotly.express as px
import streamlit as st

from app.database import SessionLocal
from app.models import Employee
from app.services.dashboard_service import DashboardService
from app.services.employee_service import EmployeeService
from app.services.leave_service import LeaveService
from app.services.attendance_service import AttendanceService
from app.services.announcement_service import AnnouncementService
from app.services.payslip_service import PayslipService


# ============================================================
# PAGE CONFIGURATION
# ============================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="HR Command Center",
        page_icon="👥",
        layout="wide",
        initial_sidebar_state="expanded",
    )


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# DESIGN SYSTEM
# ============================================================

PRIMARY = "#2563eb"
PRIMARY_DARK = "#1d4ed8"
TEXT = "#0f172a"
MUTED = "#64748b"
BORDER = "#e2e8f0"
SURFACE = "#ffffff"
BACKGROUND = "#f8fafc"
SUCCESS = "#16a34a"
WARNING = "#d97706"
DANGER = "#dc2626"


def safe_text(value: object) -> str:
    """Safely escape values before rendering them as HTML."""
    return escape("" if value is None else str(value))


def display_text(value: object) -> str:
    """Format text for display without modifying the database value."""

    if value is None:
        return "Not Available"

    text = str(value).strip()

    if not text:
        return "Not Available"

    # Preserve email addresses and identifiers.
    if "@" in text:
        return text

    # Standardize known employee statuses.
    status_map = {
        "active": "Active",
        "inactive": "Inactive",
        "on_leave": "On Leave",
        "on leave": "On Leave",
    }

    normalized = text.lower()

    if normalized in status_map:
        return status_map[normalized]

    # Format human-readable text for display.
    return text.replace("_", " ").title()


def full_name(employee: Employee) -> str:
    """Return the employee's full name."""

    return (
        f"{employee.first_name.strip()} "
        f"{employee.last_name.strip()}"
    ).strip()


# ============================================================
# STYLING
# ============================================================

def inject_styles() -> None:
    """Apply the premium HR dashboard design system."""
    from app.ui.theme import get_theme_css
    theme = st.session_state.get("theme", "dark")
    is_dark = (theme == "dark")

    theme_bg = "#080c16" if is_dark else "#f8fafc"
    theme_surface = "#0f172a" if is_dark else "#ffffff"
    theme_border = "rgba(148, 163, 184, 0.16)" if is_dark else "#e2e8f0"
    theme_text = "#f8fafc" if is_dark else "#0f172a"
    theme_muted = "#94a3b8" if is_dark else "#334155"
    card_extra = get_theme_css(theme)

    st.html(
        f"""
        <style>
        :root {{
            --primary: {PRIMARY};
            --primary-dark: {PRIMARY_DARK};
            --text: {theme_text};
            --muted: {theme_muted};
            --border: {theme_border};
            --surface: {theme_surface};
            --background: {theme_bg};
            --success: {SUCCESS};
            --warning: {WARNING};
            --danger: {DANGER};
        }}

        .stApp {{
            background: var(--background) !important;
            color: var(--text) !important;
        }}

        {card_extra}

        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }}

        /* PREMIUM SIDEBAR */

        [data-testid="stSidebar"] {{
            background: linear-gradient(
                180deg,
                #0b1220 0%,
                #111c32 55%,
                #0b1220 100%
            ) !important;
            border-right: 1px solid rgba(148, 163, 184, 0.16);
        }}

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
            color: #e2e8f0;
        }}

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            color: #f8fafc !important;
            letter-spacing: -0.35px;
        }}

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
            color: #b6c4d8 !important;
        }}

        [data-testid="stSidebar"] hr {{
            border-color: rgba(148, 163, 184, 0.18);
            margin-top: 18px;
            margin-bottom: 18px;
        }}

        [data-testid="stSidebar"] [data-testid="stRadio"] {{
            padding: 12px 10px;
            border: 1px solid rgba(148, 163, 184, 0.12);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.035);
        }}

        [data-testid="stSidebar"] [data-testid="stRadio"] label {{
            padding: 8px 10px;
            border-radius: 10px;
            transition: background 0.2s ease;
        }}

        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
            background: rgba(59, 130, 246, 0.14);
        }}

        [data-testid="stSidebar"] [data-testid="stRadio"] p {{
            color: #e2e8f0 !important;
            font-weight: 600;
        }}

        [data-testid="stSidebar"] .stButton > button {{
            min-height: 44px;
            border: 1px solid rgba(248, 113, 113, 0.30);
            border-radius: 12px;
            background: rgba(239, 68, 68, 0.09);
            color: #fecaca !important;
            font-weight: 700;
            transition: all 0.2s ease;
        }}

        [data-testid="stSidebar"] .stButton > button:hover {{
            background: rgba(239, 68, 68, 0.18);
            border-color: rgba(248, 113, 113, 0.65);
        }}

        /* HERO */

        .hr-hero {{
            background: linear-gradient(
                135deg,
                #0f172a 0%,
                #172554 52%,
                #1d4ed8 100%
            );
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 22px;
            padding: 30px 32px;
            margin-bottom: 25px;
            color: #ffffff;
            box-shadow: 0 14px 32px rgba(15, 23, 42, 0.13);
        }}

        .hr-hero,
        .hr-hero * {{
            color: #ffffff !important;
        }}

        .hr-hero-title {{
            font-size: 31px;
            font-weight: 850;
            letter-spacing: -0.8px;
            line-height: 1.3;
            margin-bottom: 8px;
        }}

        .hr-hero-subtitle {{
            color: #cbd5e1 !important;
            font-size: 14px;
            line-height: 1.7;
            margin-bottom: 18px;
        }}

        .hero-badge {{
            display: inline-block;
            padding: 7px 12px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.10);
            border: 1px solid rgba(255, 255, 255, 0.20);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.4px;
        }}

        /* SECTION HEADINGS */

        .section-title {{
            color: var(--text) !important;
            font-size: 20px;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: 0.7px;
            line-height: 1.5;
            margin-top: 12px;
            margin-bottom: 5px;
        }}

        .section-subtitle {{
            color: #64748b !important;
            font-size: 13px;
            line-height: 1.7;
            margin-bottom: 17px;
        }}

        /* KPI CARDS */

        .metric-card {{
            box-sizing: border-box;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            padding: 22px 20px;
            min-height: 138px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.045);
            transition:
                transform 0.2s ease,
                box-shadow 0.2s ease,
                border-color 0.2s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-3px);
            border-color: #bfdbfe;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.09);
        }}

        .metric-label {{
            color: #64748b !important;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1px;
            line-height: 1.6;
            overflow-wrap: anywhere;
        }}

        .metric-value {{
            color: var(--text) !important;
            font-size: 32px;
            font-weight: 850;
            line-height: 1.3;
            margin-top: 12px;
            letter-spacing: -0.8px;
            overflow-wrap: anywhere;
        }}

        .metric-note {{
            color: #64748b !important;
            font-size: 12px;
            font-weight: 500;
            line-height: 1.5;
            margin-top: 7px;
        }}

        /* PANELS */

        .panel {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            padding: 21px;
            box-shadow: 0 4px 15px rgba(15, 23, 42, 0.04);
            margin-bottom: 16px;
            color: #0f172a !important;
        }}

        .panel strong {{
            color: var(--text) !important;
            font-size: 15px;
            font-weight: 800;
        }}

        .panel small {{
            color: #64748b !important;
            font-size: 12px;
            line-height: 1.7;
        }}

        /* ALERTS */

        .alert {{
            border-radius: 13px;
            padding: 14px 16px;
            margin: 9px 0;
            font-size: 13px;
            font-weight: 600;
            line-height: 1.6;
        }}

        .alert-warning {{
            background: #fffbeb;
            border: 1px solid #fde68a;
            color: #92400e !important;
        }}

        .alert-success {{
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            color: #166534 !important;
        }}

        .alert-danger {{
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #991b1b !important;
        }}

        /* EMPLOYEE PROFILE */

        .profile-card {{
            background: linear-gradient(145deg, #ffffff, #f8fafc);
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 16px;
            box-shadow: 0 5px 18px rgba(15, 23, 42, 0.04);
        }}

        .profile-name {{
            font-size: 23px;
            font-weight: 850;
            line-height: 1.5;
            color: var(--text) !important;
        }}

        .profile-id {{
            color: #2563eb !important;
            font-size: 13px;
            font-weight: 750;
            margin-top: 3px;
        }}

        .profile-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 13px;
            margin-top: 20px;
        }}

        .profile-item {{
            background: #f8fafc;
            border-radius: 12px;
            padding: 14px;
            border: 1px solid #edf2f7;
        }}

        .profile-item-label {{
            color: #64748b !important;
            font-size: 10px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }}

        .profile-item-value {{
            color: var(--text) !important;
            font-weight: 700;
            font-size: 13px;
            line-height: 1.6;
            margin-top: 5px;
            overflow-wrap: anywhere;
        }}

        /* GENERAL WIDGET POLISH */

        [data-testid="stMetric"] {{
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 15px !important;
            padding: 17px !important;
            box-shadow: 0 3px 12px rgba(15, 23, 42, 0.035) !important;
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--muted) !important;
            font-weight: 750 !important;
        }}

        [data-testid="stMetricValue"] {{
            color: var(--text) !important;
            font-weight: 850 !important;
        }}

        [data-testid="stDataFrame"] {{
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
        }}

        .stButton > button {{
            border-radius: 11px;
            font-weight: 650;
            transition: all 0.2s ease;
        }}

        .stTextInput input,
        .stSelectbox [data-baseweb="select"],
        .stNumberInput input {{
            border-radius: 10px;
        }}

        .footer {{
            text-align: center;
            color: #64748b !important;
            font-size: 11px;
            line-height: 1.8;
            padding: 28px 0 8px;
        }}

        @media (max-width: 900px) {{
            .hr-hero {{
                padding: 23px 20px;
            }}

            .hr-hero-title {{
                font-size: 25px;
            }}

            .metric-card {{
                padding: 16px;
                min-height: 125px;
            }}

            .metric-value {{
                font-size: 27px;
            }}

            .profile-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        @media (prefers-reduced-motion: reduce) {{
            *,
            *::before,
            *::after {{
                transition-duration: 0.01ms !important;
                animation-duration: 0.01ms !important;
            }}
        }}
        </style>
        """
    )


# ============================================================
# SESSION AND AUTHORIZATION
# ============================================================

def validate_hr_session() -> bool:
    """Check authentication and HR role before showing the dashboard."""

    if not st.session_state.get("authenticated"):
        st.error("Authentication required.")
        return False

    if st.session_state.get("role") != "hr":
        st.error("You are not authorized to access the HR Dashboard.")
        return False

    return True


def render_sidebar() -> str:
    """Render HR navigation and logout control."""

    username = st.session_state.get("username") or "HR User"

    st.sidebar.html(
        f"""
        <div style="padding:20px 16px;margin:6px 0 18px 0;
                    border:1px solid rgba(129,140,248,.30);
                    border-radius:18px;
                    background:linear-gradient(145deg,#1e293b,#111c32,#0b1220);
                    box-shadow:0 12px 28px rgba(0,0,0,.24);">
            <div style="width:44px;height:44px;display:flex;
                        align-items:center;justify-content:center;
                        border-radius:13px;
                        background:linear-gradient(135deg,#818cf8,#2563eb);
                        font-size:22px;margin-bottom:15px;">👥</div>
            <div style="color:#f8fafc;font-size:16px;font-weight:800;
                        letter-spacing:.8px;line-height:1.5;">
                HR COMMAND CENTER
            </div>
            <div style="height:3px;width:46px;margin:12px 0 16px 0;
                        border-radius:10px;
                        background:linear-gradient(90deg,#818cf8,#38bdf8);">
            </div>
            <div style="color:#94a3b8;font-size:10px;font-weight:700;
                        letter-spacing:1.2px;margin-bottom:8px;">
                SIGNED IN AS
            </div>
            <div style="display:inline-block;max-width:100%;
                        box-sizing:border-box;padding:8px 11px;
                        border:1px solid rgba(96,165,250,.28);
                        border-radius:10px;
                        background:rgba(59,130,246,.12);
                        color:#bfdbfe;font-size:12px;font-weight:750;
                        letter-spacing:.7px;overflow-wrap:anywhere;">
                {safe_text(username).upper()}
            </div>
        </div>
        """
    )

    st.sidebar.html('<div style="color:#94a3b8;font-size:10px;font-weight:700;letter-spacing:1.2px;margin:10px 0 6px 0;">APPEARANCE</div>')
    current_theme = st.session_state.get("theme", "dark")
    is_dark = (current_theme == "dark")
    hr_theme_toggle = st.sidebar.toggle(
        "🌙 Dark Mode" if is_dark else "☀️ Light Mode",
        value=is_dark,
        key="hr_theme_toggle",
    )
    new_theme = "dark" if hr_theme_toggle else "light"
    if new_theme != current_theme:
        st.session_state["theme"] = new_theme
        st.rerun()

    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigation",
        [
            "Command Center",
            "Employees",
            "Employee Profile",
            "Leave Management",
            "Attendance Tracker",
            "Notice Board",
            "Payslip Generator",
            "Workforce Analytics",
            "Data Quality",
            "Onboarding",
        ],
        key="hr_navigation",
    )

    st.sidebar.divider()
    st.sidebar.caption("HR OPERATIONS")
    st.sidebar.caption("• Workforce management")
    st.sidebar.caption("• Employee lifecycle")
    st.sidebar.caption("• Data quality")
    st.sidebar.caption("• Workforce insights")
    st.sidebar.divider()

    if st.sidebar.button(
        "Logout",
        width="stretch",
        type="secondary",
    ):
        for key in (
            "authenticated",
            "user_id",
            "username",
            "role",
        ):
            st.session_state[key] = (
                False if key == "authenticated" else None
            )

        st.rerun()

    return page


# ============================================================
# HERO SECTION
# ============================================================

def render_hero() -> None:
    """Render the dashboard's main header."""

    username = st.session_state.get("username") or "HR Professional"

    st.html(
        f"""
        <div class="hr-hero">
            <div class="hr-hero-title">HR COMMAND CENTER</div>

            <div class="hr-hero-subtitle">
                Workforce operations, employee intelligence,
                onboarding and data-quality management.
            </div>

            <span class="hero-badge">
                HR • {safe_text(username)} • Live Database
            </span>
        </div>
        """
    )


# ============================================================
# KPI CARDS
# ============================================================

def render_kpis(dashboard: dict) -> None:
    """Display key workforce metrics."""

    st.html(
        """
        <div class="section-title">WORKFORCE OVERVIEW</div>

        <div class="section-subtitle">
            Current workforce status from the application database.
        </div>
        """
    )

    columns = st.columns(5)

    metrics = [
        (
            "TOTAL EMPLOYEES",
            dashboard["total_employees"],
            "Complete workforce",
        ),
        (
            "ACTIVE",
            dashboard["active_employees"],
            "Currently active",
        ),
        (
            "INACTIVE",
            dashboard["inactive_employees"],
            "Inactive records",
        ),
        (
            "ON LEAVE",
            dashboard["on_leave_employees"],
            "Current leave status",
        ),
        (
            "NEW JOINERS",
            dashboard["current_month_joiners"],
            "Joined this month",
        ),
    ]

    for column, (label, value, note) in zip(columns, metrics):
        with column:
            st.html(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        {safe_text(label)}
                    </div>

                    <div class="metric-value">
                        {safe_text(value)}
                    </div>

                    <div class="metric-note">
                        {safe_text(note)}
                    </div>
                </div>
                """
            )


# ============================================================
# DATA QUALITY CALCULATIONS
# ============================================================

def calculate_profile_quality(
    employees: list[Employee],
) -> dict:
    """Count missing employee profile fields."""

    quality = {
        "missing_email": 0,
        "missing_phone": 0,
        "missing_department": 0,
        "missing_designation": 0,
    }

    for employee in employees:
        if not employee.email or not employee.email.strip():
            quality["missing_email"] += 1

        if not employee.phone or not employee.phone.strip():
            quality["missing_phone"] += 1

        if not employee.department or not employee.department.strip():
            quality["missing_department"] += 1

        if not employee.designation or not employee.designation.strip():
            quality["missing_designation"] += 1

    return quality


# ============================================================
# HR ALERTS
# ============================================================

def render_alerts(
    employees: list[Employee],
    dashboard: dict,
) -> None:
    """Show HR alerts based on actual dashboard data."""

    quality = calculate_profile_quality(employees)
    alerts: list[tuple[str, str]] = []

    missing_total = sum(quality.values())

    if missing_total:
        alerts.append(
            (
                "warning",
                f"{missing_total} profile data-quality issue(s) "
                "require HR review.",
            )
        )

    if dashboard["inactive_employees"] > 0:
        alerts.append(
            (
                "warning",
                f"{dashboard['inactive_employees']} inactive "
                "employee record(s) are present.",
            )
        )

    if dashboard["on_leave_employees"] > 0:
        alerts.append(
            (
                "warning",
                f"{dashboard['on_leave_employees']} employee(s) "
                "are currently marked on leave.",
            )
        )

    if not alerts:
        alerts.append(
            ("success", "No immediate HR operational alerts detected.")
        )

    st.html(
        """
        <div class="section-title">HR ALERTS</div>

        <div class="section-subtitle">
            Operational items requiring attention.
        </div>
        """
    )

    css_classes = {
        "warning": "alert-warning",
        "danger": "alert-danger",
        "success": "alert-success",
    }

    for level, message in alerts:
        css_class = css_classes.get(level, "alert-warning")

        st.html(
            f"""
            <div class="alert {css_class}">
                {safe_text(message)}
            </div>
            """
        )


# ============================================================
# COMMAND CENTER
# ============================================================

def render_command_center(
    dashboard: dict,
    employees: list[Employee],
) -> None:
    """Render the main HR overview."""

    render_hero()
    render_kpis(dashboard)

    st.divider()

    left, right = st.columns([1.4, 1])

    with left:
        render_alerts(employees, dashboard)

        st.html(
            """
            <div class="section-title">DEPARTMENT OVERVIEW</div>

            <div class="section-subtitle">
                Workforce distribution by department.
            </div>
            """
        )

        department_data = [
            {
                "Department": display_text(department),
                "Employees": count,
            }
            for department, count in dashboard["department_counts"]
        ]

        if department_data:
            st.dataframe(
                department_data,
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No department data available.")

    with right:
        st.html(
            """
            <div class="section-title">RECENT EMPLOYEES</div>

            <div class="section-subtitle">
                Latest employee records.
            </div>
            """
        )

        recent = dashboard["recent_employees"]

        if recent:
            st.dataframe(
                [
                    {
                        "ID": employee.employee_id,
                        "Name": display_text(full_name(employee)),
                        "Department": display_text(employee.department),
                        "Status": display_text(employee.status),
                    }
                    for employee in recent
                ],
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No employees available.")

    st.divider()

    st.html(
        """
        <div class="section-title">QUICK HR ACTIONS</div>

        <div class="section-subtitle">
            Frequently used workforce operations.
        </div>
        """
    )

    action_columns = st.columns(4)

    actions = [
        ("🔎 Search Employees", "Employees"),
        ("👤 Employee Profile", "Employee Profile"),
        ("📊 Workforce Analytics", "Workforce Analytics"),
        ("🧹 Data Quality", "Data Quality"),
    ]

    for column, (label, target_page) in zip(action_columns, actions):
        with column:
            if st.button(label, width="stretch"):
                st.session_state["hr_page"] = target_page
                st.rerun()


# ============================================================
# EMPLOYEE SEARCH
# ============================================================

def render_employees(
    employee_service: EmployeeService,
) -> None:
    """Render employee search and paginated results."""

    st.html(
        """
        <div class="section-title">EMPLOYEE MANAGEMENT</div>

        <div class="section-subtitle">
            Workforce search with department, designation and status filters.
        </div>
        """
    )

    search_term = st.text_input(
        "Search",
        placeholder=(
            "Employee ID, name, email, phone, department or designation"
        ),
    )

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        department = st.text_input(
            "Department",
            placeholder="Example: IT",
        )

    with filter_col2:
        designation = st.text_input(
            "Designation",
            placeholder="Example: SWE 3",
        )

    with filter_col3:
        status = st.selectbox(
            "Status",
            ["All", "active", "inactive", "on_leave"],
        )

    page_size = st.selectbox(
        "Records per page",
        [10, 20, 50, 100],
        index=1,
    )

    page = st.number_input(
        "Page",
        min_value=1,
        value=1,
        step=1,
    )

    try:
        employees = employee_service.search_employees(
            search_term=search_term.strip(),
            department=department.strip() or None,
            designation=designation.strip() or None,
            status=None if status == "All" else status,
            page=int(page),
            page_size=page_size,
        )
    except ValueError as exc:
        st.error(str(exc))
        return

    st.caption(
        f"Showing up to {page_size} records for page {int(page)}."
    )

    if not employees:
        st.info("No employees matched the selected criteria.")
        return

    st.dataframe(
        [
            {
                "Employee ID": employee.employee_id,
                "Name": display_text(full_name(employee)),
                "Email": employee.email,
                "Phone": employee.phone,
                "Department": display_text(employee.department),
                "Designation": display_text(employee.designation),
                "Joining Date": employee.joining_date,
                "Status": display_text(employee.status),
            }
            for employee in employees
        ],
        width="stretch",
        hide_index=True,
    )


# ============================================================
# EMPLOYEE PROFILE
# ============================================================

def render_employee_profile(
    employee_service: EmployeeService,
) -> None:
    """Show one employee's profile."""

    st.html(
        """
        <div class="section-title">EMPLOYEE PROFILE</div>

        <div class="section-subtitle">
            Inspect an employee record from the database.
        </div>
        """
    )

    employee_id = st.text_input(
        "Employee ID",
        placeholder="Example: emp001",
    ).strip()

    if not employee_id:
        st.info("Enter an Employee ID to view the profile.")
        return

    try:
        employee = employee_service.get_employee_by_id(employee_id)
    except ValueError as exc:
        st.error(str(exc))
        return

    if employee is None:
        st.warning("Employee not found.")
        return

    status_class = (
        "alert-success"
        if str(employee.status).strip().lower() == "active"
        else "alert-warning"
    )

    st.html(
        f"""
        <div class="profile-card">
            <div class="profile-name">
                {safe_text(display_text(full_name(employee)))}
            </div>

            <div class="profile-id">
                {safe_text(employee.employee_id)}
            </div>

            <div class="profile-grid">
                <div class="profile-item">
                    <div class="profile-item-label">EMAIL</div>
                    <div class="profile-item-value">
                        {safe_text(employee.email)}
                    </div>
                </div>

                <div class="profile-item">
                    <div class="profile-item-label">PHONE</div>
                    <div class="profile-item-value">
                        {safe_text(employee.phone)}
                    </div>
                </div>

                <div class="profile-item">
                    <div class="profile-item-label">DEPARTMENT</div>
                    <div class="profile-item-value">
                        {safe_text(display_text(employee.department))}
                    </div>
                </div>

                <div class="profile-item">
                    <div class="profile-item-label">DESIGNATION</div>
                    <div class="profile-item-value">
                        {safe_text(display_text(employee.designation))}
                    </div>
                </div>

                <div class="profile-item">
                    <div class="profile-item-label">JOINING DATE</div>
                    <div class="profile-item-value">
                        {safe_text(employee.joining_date)}
                    </div>
                </div>

                <div class="profile-item">
                    <div class="profile-item-label">STATUS</div>
                    <div class="profile-item-value">
                        {safe_text(display_text(employee.status))}
                    </div>
                </div>
            </div>

            <div class="alert {status_class}" style="margin-top:18px;">
                Employee record loaded from the database.
            </div>
        </div>
        """
    )


# ============================================================
# SHARED PLOTLY CONFIGURATION
# ============================================================

def style_distribution_chart(
    figure,
    *,
    title: str,
    category_axis: str,
    value_axis: str,
    item_count: int,
    max_value: int,
):
    """Style horizontal workforce distribution charts."""

    chart_height = min(
        560,
        max(300, 210 + item_count * 38),
    )

    axis_max = max(1, max_value) * 1.30

    figure.update_traces(
        marker=dict(
            color=PRIMARY,
            line=dict(
                color=PRIMARY_DARK,
                width=0.5,
            ),
        ),
        textposition="outside",
        cliponaxis=False,
        textfont=dict(
            color="#000000",
            size=13,
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=BORDER,
            font=dict(
                color="#000000",
                size=13,
            ),
        ),
    )

    figure.update_layout(
        height=chart_height,
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(
            family="Arial, sans-serif",
            size=13,
            color="#000000",
        ),
        title=dict(
            text=title,
            font=dict(
                size=21,
                color="#000000",
            ),
            x=0.02,
            xanchor="left",
        ),
        showlegend=False,
        bargap=0.55,
        margin=dict(
            l=35,
            r=65,
            t=70,
            b=55,
        ),
        hovermode="closest",
    )

    figure.update_yaxes(
        title=dict(
            text=category_axis,
            font=dict(color="#000000", size=14),
        ),
        tickfont=dict(
            color="#000000",
            size=12,
        ),
        categoryorder="total ascending",
        showgrid=False,
        showline=True,
        linecolor="#94a3b8",
        linewidth=1,
        automargin=True,
        fixedrange=False,
    )

    figure.update_xaxes(
        title=dict(
            text=value_axis,
            font=dict(color="#000000", size=14),
        ),
        tickfont=dict(
            color="#000000",
            size=12,
        ),
        range=[0, axis_max],
        rangemode="tozero",
        showgrid=True,
        gridcolor="rgba(100,116,139,0.18)",
        zeroline=True,
        zerolinecolor="#94a3b8",
        showline=True,
        linecolor="#94a3b8",
        linewidth=1,
        automargin=True,
    )

    return figure


# ============================================================
# WORKFORCE ANALYTICS
# ============================================================

def render_workforce_analytics(
    dashboard: dict,
    dashboard_service: DashboardService,
) -> None:
    """Render hiring trends and workforce distribution charts."""

    st.html(
        """
        <div class="section-title">WORKFORCE ANALYTICS</div>

        <div class="section-subtitle">
            Management-level workforce distribution and insights.
        </div>
        """
    )

    st.html(
        """
        <div class="panel">
            <strong>MONTHLY HIRING TREND</strong>
            <br>
            <small>
                Employee joiners grouped by their actual joining dates.
            </small>
        </div>
        """
    )

    months_to_show = st.selectbox(
        "Analysis period",
        options=[3, 6, 12, 24],
        index=1,
        format_func=lambda value: f"Last {value} calendar months",
        key="workforce_hiring_period",
    )

    hiring_trend = dashboard_service.get_monthly_hiring_trend(
        months=months_to_show
    )

    if hiring_trend:
        hiring_data = [
            {
                "Month": month,
                "New Joiners": count,
            }
            for month, count in hiring_trend
        ]

        hiring_frame = pd.DataFrame(hiring_data)

        hiring_fig = px.line(
            hiring_frame,
            x="Month",
            y="New Joiners",
            title="Monthly Hiring Trend",
            markers=True,
            labels={
                "Month": "Month",
                "New Joiners": "Employees Joined",
            },
            template="plotly_white",
        )

        hiring_fig.update_traces(
            line=dict(
                color=PRIMARY,
                width=3,
            ),
            marker=dict(
                color=PRIMARY,
                size=9,
                line=dict(
                    color="#FFFFFF",
                    width=1,
                ),
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Employees Joined: %{y}"
                "<extra></extra>"
            ),
        )

        hiring_fig.update_layout(
            height=420,
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=dict(
                family="Arial, sans-serif",
                color="#000000",
                size=14,
            ),
            title=dict(
                text="Monthly Hiring Trend",
                font=dict(
                    color="#000000",
                    size=22,
                ),
                x=0.02,
                xanchor="left",
            ),
            hovermode="x unified",
            hoverlabel=dict(
                font=dict(color="#000000"),
                bgcolor="#FFFFFF",
            ),
            margin=dict(
                l=55,
                r=30,
                t=70,
                b=55,
            ),
        )

        hiring_fig.update_xaxes(
            title=dict(
                text="Month",
                font=dict(color="#000000"),
            ),
            tickfont=dict(color="#000000"),
            showgrid=False,
            showline=True,
            linecolor="#94a3b8",
            automargin=True,
        )

        hiring_fig.update_yaxes(
            title=dict(
                text="Employees Joined",
                font=dict(color="#000000"),
            ),
            tickfont=dict(color="#000000"),
            rangemode="tozero",
            gridcolor="rgba(100,116,139,0.18)",
            zerolinecolor="#94a3b8",
            showline=True,
            linecolor="#94a3b8",
            automargin=True,
        )

        st.plotly_chart(
            hiring_fig,
            width="stretch",
            config={
                "displaylogo": False,
                "scrollZoom": True,
                "responsive": True,
            },
        )

        with st.expander("VIEW MONTHLY HIRING DATA"):
            st.dataframe(
                hiring_data,
                width="stretch",
                hide_index=True,
            )
    else:
        st.info("No monthly hiring data is available.")

    st.divider()

    left, right = st.columns(2, gap="large")

    # DEPARTMENT DISTRIBUTION

    with left:
        st.html(
            """
            <div class="panel">
                <strong>DEPARTMENT DISTRIBUTION</strong>
                <br>
                <small>Employees grouped by department.</small>
            </div>
            """
        )

        department_data = [
            {
                "Department": display_text(department)
                if department
                else "Unassigned",
                "Employees": count,
            }
            for department, count in dashboard["department_counts"]
        ]

        if department_data:
            department_data.sort(
                key=lambda item: item["Employees"],
                reverse=True,
            )

            department_fig = px.bar(
                department_data,
                x="Employees",
                y="Department",
                orientation="h",
                title="Employees by Department",
                text="Employees",
                labels={
                    "Employees": "Number of Employees",
                    "Department": "Department",
                },
                template="plotly_white",
            )

            max_department_count = max(
                item["Employees"]
                for item in department_data
            )

            department_fig = style_distribution_chart(
                department_fig,
                title="Employees by Department",
                category_axis="Department",
                value_axis="Number of Employees",
                item_count=len(department_data),
                max_value=max_department_count,
            )

            department_fig.update_traces(
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Employees: %{x}"
                    "<extra></extra>"
                ),
            )

            st.plotly_chart(
                department_fig,
                width="stretch",
                config={
                    "displaylogo": False,
                    "scrollZoom": False,
                    "responsive": True,
                },
            )

            with st.expander("VIEW DEPARTMENT DATA"):
                st.dataframe(
                    department_data,
                    width="stretch",
                    hide_index=True,
                )
        else:
            st.info("No department data is available.")

    # DESIGNATION DISTRIBUTION

    with right:
        st.html(
            """
            <div class="panel">
                <strong>DESIGNATION DISTRIBUTION</strong>
                <br>
                <small>Employees grouped by designation.</small>
            </div>
            """
        )

        designation_data = [
            {
                "Designation": display_text(designation)
                if designation
                else "Unassigned",
                "Employees": count,
            }
            for designation, count in dashboard["designation_counts"]
        ]

        if designation_data:
            designation_data.sort(
                key=lambda item: item["Employees"],
                reverse=True,
            )

            designation_fig = px.bar(
                designation_data,
                x="Employees",
                y="Designation",
                orientation="h",
                title="Employees by Designation",
                text="Employees",
                labels={
                    "Employees": "Number of Employees",
                    "Designation": "Designation",
                },
                template="plotly_white",
            )

            max_designation_count = max(
                item["Employees"]
                for item in designation_data
            )

            designation_fig = style_distribution_chart(
                designation_fig,
                title="Employees by Designation",
                category_axis="Designation",
                value_axis="Number of Employees",
                item_count=len(designation_data),
                max_value=max_designation_count,
            )

            designation_fig.update_traces(
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Employees: %{x}"
                    "<extra></extra>"
                ),
            )

            st.plotly_chart(
                designation_fig,
                width="stretch",
                config={
                    "displaylogo": False,
                    "scrollZoom": False,
                    "responsive": True,
                },
            )

            with st.expander("VIEW DESIGNATION DATA"):
                st.dataframe(
                    designation_data,
                    width="stretch",
                    hide_index=True,
                )
        else:
            st.info("No designation data is available.")

    st.divider()

    st.html(
        """
        <div class="section-title">WORKFORCE INSIGHTS</div>
        """
    )

    total = dashboard["total_employees"]

    if total:
        active_ratio = (
            dashboard["active_employees"] / total
        ) * 100

        leave_ratio = (
            dashboard["on_leave_employees"] / total
        ) * 100

        metric_columns = st.columns(2)

        with metric_columns[0]:
            st.metric(
                "ACTIVE WORKFORCE",
                f"{active_ratio:.1f}%",
                help=(
                    "Percentage of all employees whose status is active."
                ),
            )

        with metric_columns[1]:
            st.metric(
                "EMPLOYEES ON LEAVE",
                f"{leave_ratio:.1f}%",
                help=(
                    "Percentage of all employees currently marked on leave."
                ),
            )

        st.progress(
            min(max(active_ratio / 100, 0.0), 1.0),
            text="Active workforce",
        )
    else:
        st.info("No employee records are available for analysis.")


# ============================================================
# DATA QUALITY PAGE
# ============================================================

def render_data_quality(
    employees: list[Employee],
) -> None:
    """Display missing employee profile information."""

    st.html(
        """
        <div class="section-title">EMPLOYEE DATA QUALITY</div>

        <div class="section-subtitle">
            Identify incomplete employee profiles without
            modifying existing records.
        </div>
        """
    )

    quality = calculate_profile_quality(employees)
    columns = st.columns(4)

    items = [
        ("MISSING EMAIL", quality["missing_email"]),
        ("MISSING PHONE", quality["missing_phone"]),
        ("MISSING DEPARTMENT", quality["missing_department"]),
        ("MISSING DESIGNATION", quality["missing_designation"]),
    ]

    for column, (label, value) in zip(columns, items):
        with column:
            st.metric(label, value)

    incomplete_ids = []

    for employee in employees:
        incomplete = (
            not employee.email
            or not employee.email.strip()
            or not employee.phone
            or not employee.phone.strip()
            or not employee.department
            or not employee.department.strip()
            or not employee.designation
            or not employee.designation.strip()
        )

        if incomplete:
            incomplete_ids.append(employee.employee_id)

    st.divider()

    if incomplete_ids:
        st.warning(
            f"{len(incomplete_ids)} employee profile(s) "
            "need data-quality review."
        )

        st.dataframe(
            [
                {"Employee ID": employee_id}
                for employee_id in incomplete_ids
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.success(
            "All currently loaded employee profiles contain "
            "the required profile fields."
        )


# ============================================================
# ONBOARDING PAGE
# ============================================================

def render_onboarding(
    employees: list[Employee],
) -> None:
    """Show upcoming joining records and profile readiness."""

    st.html(
        """
        <div class="section-title">EMPLOYEE ONBOARDING</div>

        <div class="section-subtitle">
            New-joiner tracking based on employee joining dates.
        </div>
        """
    )

    today = date.today()

    new_joiners = [
        employee
        for employee in employees
        if employee.joining_date
        and employee.joining_date >= today
    ]

    if not new_joiners:
        st.info("No future-dated employee joining records were found.")
    else:
        st.dataframe(
            [
                {
                    "Employee ID": employee.employee_id,
                    "Name": display_text(full_name(employee)),
                    "Department": display_text(employee.department),
                    "Designation": display_text(employee.designation),
                    "Joining Date": employee.joining_date,
                    "Status": display_text(employee.status),
                }
                for employee in sorted(
                    new_joiners,
                    key=lambda item: item.joining_date,
                )
            ],
            width="stretch",
            hide_index=True,
        )

    st.divider()

    st.html(
        """
        <div class="section-title">PROFILE READINESS</div>
        """
    )

    ready = 0
    incomplete = 0

    for employee in employees:
        complete = all(
            [
                bool(employee.first_name.strip()),
                bool(employee.last_name.strip()),
                bool(employee.email and employee.email.strip()),
                bool(employee.phone and employee.phone.strip()),
                bool(employee.department and employee.department.strip()),
                bool(employee.designation and employee.designation.strip()),
                employee.joining_date is not None,
            ]
        )

        if complete:
            ready += 1
        else:
            incomplete += 1

    column1, column2 = st.columns(2)

    with column1:
        st.metric("PROFILE READY", ready)

    with column2:
        st.metric("NEEDS REVIEW", incomplete)


def render_hr_leaves(db, employees: list[Employee]) -> None:
    st.html(
        """
        <div class="section-title">LEAVE MANAGEMENT & APPROVALS</div>
        <div class="section-subtitle">
            Review time-off requests submitted by employees, track leave balances, and approve or decline requests.
        </div>
        """
    )
    leave_service = LeaveService(db)
    pending_count = leave_service.count_pending()
    on_leave_today = leave_service.count_on_leave_today()
    all_leaves = leave_service.get_all_leaves(limit=200)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Pending Requests", pending_count)
    with c2:
        st.metric("On Leave Today", on_leave_today)
    with c3:
        st.metric("Approved Requests", sum(1 for l in all_leaves if l.status == "Approved"))
    with c4:
        st.metric("Declined Requests", sum(1 for l in all_leaves if l.status == "Rejected"))

    st.write("")
    f1, f2 = st.columns(2)
    with f1:
        status_filter = st.selectbox("Status Filter", ["All", "Pending", "Approved", "Rejected"], key="hr_leave_status")
    with f2:
        depts = sorted(list({e.department for e in employees if e.department}))
        dept_filter = st.selectbox("Department Filter", ["All"] + depts, key="hr_leave_dept")

    filtered = leave_service.get_all_leaves(
        status=status_filter if status_filter != "All" else None,
        department=dept_filter if dept_filter != "All" else None,
    )

    if not filtered:
        st.info("No leave requests found matching criteria.")
        return

    for l in filtered:
        emp = l.employee
        emp_name = f"{emp.first_name} {emp.last_name}" if emp else "Unknown"
        with st.container(border=True):
            r1, r2 = st.columns([3, 1])
            with r1:
                st.markdown(f"**{escape(emp_name)}** `({escape(emp.employee_id if emp else 'N/A')})` • {escape(emp.department if emp else '')}")
                st.caption(f"📌 {escape(l.leave_type)} • {l.start_date} to {l.end_date} ({l.days_count} days) • Applied: {l.applied_at.strftime('%Y-%m-%d %H:%M')}")
            with r2:
                st.write(f"**Status: {l.status}**")

            st.write(f"Reason: *{escape(l.reason)}*")

            if l.status == "Pending":
                with st.form(f"hr_leave_form_{l.id}"):
                    remarks = st.text_input("Remarks", placeholder="Add approval or decline note...")
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        app_btn = st.form_submit_button("✅ Approve", type="primary", width="stretch")
                    with bc2:
                        rej_btn = st.form_submit_button("❌ Decline", type="secondary", width="stretch")

                    if app_btn:
                        leave_service.review_leave(l.id, "Approved", remarks, actor_username=st.session_state.get("username", "HR"))
                        st.success("Leave approved.")
                        st.rerun()
                    if rej_btn:
                        leave_service.review_leave(l.id, "Rejected", remarks, actor_username=st.session_state.get("username", "HR"))
                        st.warning("Leave declined.")
                        st.rerun()
            else:
                if l.admin_remarks:
                    st.caption(f"Remarks: {escape(l.admin_remarks)}")


def render_hr_attendance(db, employees: list[Employee]) -> None:
    st.html(
        """
        <div class="section-title">DAILY ATTENDANCE MONITOR</div>
        <div class="section-subtitle">
            Real-time workforce presence, late arrival analysis, and attendance compliance logs.
        </div>
        """
    )
    attendance_service = AttendanceService(db)

    selected_date = st.date_input("Attendance Date", value=date.today(), key="hr_att_date")
    summary = attendance_service.get_daily_summary(selected_date)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Workforce", summary["total_active_employees"])
    with m2:
        st.metric("Present Today", summary["present_count"])
    with m3:
        st.metric("Late Arrivals", summary["late_count"])
    with m4:
        st.metric("Attendance Rate", f"{summary['attendance_rate']}%")

    records = summary["records"]
    if not records:
        st.info(f"No attendance logs recorded for {selected_date}.")
    else:
        table = [
            {
                "Employee ID": r.employee.employee_id if r.employee else "N/A",
                "Name": f"{r.employee.first_name} {r.employee.last_name}" if r.employee else "N/A",
                "Department": r.employee.department if r.employee else "N/A",
                "Clock In": r.clock_in.strftime("%I:%M %p") if r.clock_in else "Not Checked In",
                "Clock Out": r.clock_out.strftime("%I:%M %p") if r.clock_out else "Active Shift",
                "Work Hours": f"{r.work_hours:.2f} hrs",
                "Status": r.status,
            }
            for r in records
        ]
        st.dataframe(table, width="stretch", hide_index=True)


def render_hr_announcements(db) -> None:
    st.html(
        """
        <div class="section-title">COMPANY NOTICE BOARD</div>
        <div class="section-subtitle">
            Broadcast operational updates, policy news, and event reminders to employees.
        </div>
        """
    )
    ann_service = AnnouncementService(db)
    tab1, tab2 = st.tabs(["📢 Bulletins", "✍️ Post Bulletin"])

    with tab1:
        all_ann = ann_service.get_all()
        if not all_ann:
            st.info("No bulletins published.")
        for a in all_ann:
            with st.container(border=True):
                st.markdown(f"### {escape(a.title)} `[{escape(a.priority)}]`")
                st.caption(f"Posted by {escape(a.posted_by)} • Target: {a.target_role.upper()} • {a.created_at.strftime('%d %b %Y')}")
                st.write(a.content)
                if st.button("Delete Notice", key=f"hr_del_{a.id}"):
                    ann_service.delete(a.id, actor_username=st.session_state.get("username", "HR"))
                    st.success("Deleted.")
                    st.rerun()

    with tab2:
        with st.form("hr_new_notice"):
            t = st.text_input("Title")
            p = st.selectbox("Priority", ["Normal", "Important", "Urgent"])
            r = st.selectbox("Audience", ["all", "employee", "hr"])
            c = st.text_area("Body")
            if st.form_submit_button("Publish Bulletin", type="primary"):
                if t.strip() and c.strip():
                    ann_service.create_announcement(t, c, p, r, posted_by=st.session_state.get("username", "HR"))
                    st.success("Published!")
                    st.rerun()
                else:
                    st.error("Title and body are required.")


def render_hr_payslips(db, employees: list[Employee]) -> None:
    st.html(
        """
        <div class="section-title">PAYSLIP GENERATOR</div>
        <div class="section-subtitle">
            Generate and export verified monthly salary slips with automated earnings and deduction breakdowns.
        </div>
        """
    )
    if not employees:
        st.info("No employees found.")
        return

    emp_dict = {f"{e.first_name} {e.last_name} ({e.employee_id})": e for e in employees}
    c1, c2, c3 = st.columns(3)
    with c1:
        sel_name = st.selectbox("Select Employee", list(emp_dict.keys()), key="hr_ps_emp")
    with c2:
        curr_m = date.today().month
        sel_month = st.selectbox("Month", range(1, 13), index=curr_m - 1, format_func=lambda m: date(2026, m, 1).strftime("%B"), key="hr_ps_m")
    with c3:
        curr_y = date.today().year
        sel_year = st.number_input("Year", min_value=2020, max_value=2030, value=curr_y, key="hr_ps_y")

    emp = emp_dict[sel_name]
    data = PayslipService.calculate_salary_breakdown(emp, int(sel_year), int(sel_month))
    html_slip = PayslipService.generate_html_payslip(emp, int(sel_year), int(sel_month))

    with st.container(border=True):
        st.markdown(f"### {emp.first_name} {emp.last_name} • {data['pay_period']}")
        ec1, ec2 = st.columns(2)
        with ec1:
            st.markdown("#### Earnings")
            for k, v in data["earnings"].items():
                st.write(f"- **{k}:** ₹{v:,.2f}")
            st.markdown(f"**Gross:** `₹{data['total_earnings']:,.2f}`")
        with ec2:
            st.markdown("#### Deductions")
            for k, v in data["deductions"].items():
                st.write(f"- **{k}:** ₹{v:,.2f}")
            st.markdown(f"**Total Deductions:** `₹{data['total_deductions']:,.2f}`")

        st.divider()
        st.metric("Net Salary", f"₹{data['net_salary']:,.2f}")

        st.download_button(
            "📥 Download Formal Payslip (HTML)",
            data=html_slip,
            file_name=f"payslip_{emp.employee_id}_{sel_month}_{sel_year}.html",
            mime="text/html",
            type="primary",
        )


# ============================================================
# FOOTER
# ============================================================

def render_footer() -> None:
    """Render the dashboard footer."""

    st.html(
        """
        <div class="footer">
            Employee Management System • HR Command Center
            • TQM QUALITY GOAL: IMPROVE PERFORMANCE
        </div>
        """
    )


# ============================================================
# MAIN APPLICATION
# ============================================================

def main() -> None:
    """Initialize services and render the selected HR page."""

    if not validate_hr_session():
        return

    inject_styles()

    db = SessionLocal()

    try:
        dashboard_service = DashboardService(db)
        employee_service = EmployeeService(db)

        dashboard = dashboard_service.get_dashboard_summary()
        employees = employee_service.get_all_employees()

        selected_page = render_sidebar()

        page_override = st.session_state.pop("hr_page", None)

        if page_override:
            selected_page = page_override

        if selected_page == "Command Center":
            render_command_center(dashboard, employees)

        elif selected_page == "Employees":
            render_hero()
            render_employees(employee_service)

        elif selected_page == "Employee Profile":
            render_hero()
            render_employee_profile(employee_service)

        elif selected_page == "Leave Management":
            render_hero()
            render_hr_leaves(db, employees)

        elif selected_page == "Attendance Tracker":
            render_hero()
            render_hr_attendance(db, employees)

        elif selected_page == "Notice Board":
            render_hero()
            render_hr_announcements(db)

        elif selected_page == "Payslip Generator":
            render_hero()
            render_hr_payslips(db, employees)

        elif selected_page == "Workforce Analytics":
            render_hero()
            render_workforce_analytics(
                dashboard,
                dashboard_service,
            )

        elif selected_page == "Data Quality":
            render_hero()
            render_data_quality(employees)

        elif selected_page == "Onboarding":
            render_hero()
            render_onboarding(employees)

        render_footer()

    except Exception:
        logger.exception("HR dashboard operation failed.")
        st.error(
            "The HR dashboard could not complete the requested operation. "
            "Please check the application logs for technical details."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()