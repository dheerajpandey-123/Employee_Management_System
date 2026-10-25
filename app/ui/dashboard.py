import html
from datetime import date, datetime
from decimal import Decimal

import bcrypt
import streamlit as st
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Employee, User
from app.services.csv_import_service import CSVImportService
from app.services.dashboard_service import DashboardService
from app.services.employee_service import EmployeeService
from app.services.audit_log_service import AuditLogService
from app.services.leave_service import LeaveService
from app.services.attendance_service import AttendanceService
from app.services.announcement_service import AnnouncementService
from app.services.payslip_service import PayslipService


def load_dashboard_styles() -> None:
    css_path = "app/ui/dashboard_styles.css"
    theme = st.session_state.get("theme", "dark")

    base_css = ""
    try:
        with open(css_path, "r", encoding="utf-8") as css_file:
            base_css = css_file.read()
    except OSError:
        pass

    from app.ui.theme import get_theme_css
    theme_css = get_theme_css(theme)
    st.html(f"<style>{base_css}\n{theme_css}</style>")


def get_db():
    return SessionLocal()


def safe_text(value: object) -> str:
    return html.escape(str(value))


def ui_icon(name: str, size: int = 18) -> str:
    icons = {
        "users": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
            '<circle cx="9" cy="7" r="4"/>'
            '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
            '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
            "</svg>"
        ),
        "user-check": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
            '<circle cx="9" cy="7" r="4"/>'
            '<path d="m16 11 2 2 4-4"/>'
            "</svg>"
        ),
        "user-off": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M10.3 6.3a4 4 0 1 0-5.6 5.6"/>'
            '<path d="M2 21a8 8 0 0 1 12.8-6.4"/>'
            '<path d="m22 22-5-5"/>'
            '<path d="m17 17 5-5"/>'
            '<path d="M15.5 5.5a4 4 0 0 1 3.5 4"/>'
            "</svg>"
        ),
        "calendar": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<rect x="3" y="4" width="18" height="18" rx="2"/>'
            '<path d="M16 2v4M8 2v4M3 10h18"/>'
            "</svg>"
        ),
        "user-plus": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M15 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'
            '<circle cx="8" cy="7" r="4"/>'
            '<path d="M19 8v6M22 11h-6"/>'
            "</svg>"
        ),
        "building": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<rect x="3" y="3" width="18" height="18" rx="2"/>'
            '<path d="M9 21V9h6v12M7 7h2M15 7h2M7 12h2M15 12h2M7 17h2M15 17h2"/>'
            "</svg>"
        ),
        "briefcase": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<rect x="3" y="7" width="18" height="13" rx="2"/>'
            '<path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
            '<path d="M3 12h18M10 12v2h4v-2"/>'
            "</svg>"
        ),
        "activity": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M3 12h4l3-8 4 16 3-8h4"/>'
            "</svg>"
        ),
        "search": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<circle cx="11" cy="11" r="7"/>'
            '<path d="m20 20-4-4"/>'
            "</svg>"
        ),
        "upload": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M12 16V4"/>'
            '<path d="m7 9 5-5 5 5"/>'
            '<path d="M4 20h16"/>'
            "</svg>"
        ),
        "edit": (
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M12 20h9"/>'
            '<path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z"/>'
            "</svg>"
        ),
    }

    svg = icons.get(name, icons["activity"])

    return svg.replace(
        "<svg ",
        f'<svg width="{size}" height="{size}" ',
    )


def navigate_to(page: str) -> None:
    st.session_state["selected_page"] = page
    st.rerun()


def logout_admin() -> None:
    """
    Safely terminate the current Admin session.

    This only clears authentication/session information.
    No employee or user database records are modified.
    """
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["username"] = None
    st.session_state["role"] = None
    st.session_state["selected_page"] = "Dashboard"

    st.rerun()


def render_sidebar() -> str:
    # Streamlit HTML renderer is used consistently.
    st.sidebar.html(
        """
        <div class="sidebar-brand">
            <div class="sidebar-logo">EM</div>
            <div>
                <div class="sidebar-brand-name">EmployeeHub</div>
                <div class="sidebar-brand-subtitle">HR Operations</div>
            </div>
        </div>
        """
    )

    st.sidebar.html('<div class="sidebar-section-label">APPEARANCE</div>')
    current_theme = st.session_state.get("theme", "dark")
    is_dark = (current_theme == "dark")
    theme_toggle = st.sidebar.toggle(
        "🌙 Dark Mode" if is_dark else "☀️ Light Mode",
        value=is_dark,
        key="admin_theme_toggle",
    )
    new_theme = "dark" if theme_toggle else "light"
    if new_theme != current_theme:
        st.session_state["theme"] = new_theme
        st.rerun()

    st.sidebar.html(
        '<div class="sidebar-section-label">WORKSPACE</div>'
    )

    pages = [
        "Dashboard",
        "Add Employee",
        "Search Employees",
        "Update / Delete",
        "Leave Management",
        "Attendance Tracker",
        "Notice Board",
        "Payslip Generator",
        "CSV Import",
        "User Management",
        "Activity Log",
    ]

    current_page = st.session_state.get(
        "selected_page",
        "Dashboard",
    )

    if current_page not in pages:
        current_page = "Dashboard"

    selected_page = st.sidebar.radio(
        "Navigation",
        pages,
        index=pages.index(current_page),
        label_visibility="collapsed",
    )

    st.session_state["selected_page"] = selected_page

    st.sidebar.html(
        """
        <div class="sidebar-divider"></div>

        <div class="sidebar-status">
            <span class="status-dot"></span>
            <div>
                <div class="sidebar-status-title">
                    Database Connected
                </div>
                <div class="sidebar-status-text">
                    Live operational data
                </div>
            </div>
        </div>

        <div class="sidebar-footer">
            <div class="sidebar-footer-title">
                Employee Management System
            </div>
            <div class="sidebar-footer-text">
                Enterprise HR workspace
            </div>
        </div>
        """
    )

    st.sidebar.html(
        '<div class="sidebar-divider"></div>'
    )

    if st.sidebar.button(
        "Logout",
        key="admin_logout",
        icon=":material/logout:",
        width="stretch",
    ):
        logout_admin()

    return selected_page


def dashboard_page() -> None:
    load_dashboard_styles()

    db = get_db()

    try:
        dashboard = DashboardService(
            db
        ).get_dashboard_summary()
        announcements = AnnouncementService(db).get_active(target_role="all")
        pending_leaves = LeaveService(db).count_pending()
        attendance_summary = AttendanceService(db).get_daily_summary()
    finally:
        db.close()

    total = dashboard["total_employees"]
    active = dashboard["active_employees"]
    inactive = dashboard["inactive_employees"]
    on_leave = dashboard["on_leave_employees"]
    new_joiners = dashboard["current_month_joiners"]
    department_counts = dashboard["department_counts"]
    designation_counts = dashboard["designation_counts"]
    recent_employees = dashboard["recent_employees"]

    active_percentage = active / total * 100 if total else 0
    department_count = len(department_counts)
    designation_count = len(designation_counts)

    st.html(
        f"""
        <section class="v8-hero">
            <div class="v8-hero-main">
                <div class="v8-eyebrow">
                    EMPLOYEEHUB <span>/</span> HR OPERATIONS
                </div>

                <h1>Workforce Intelligence</h1>

                <p>
                    A real-time executive view of workforce health,
                    organizational structure and employee activity.
                </p>

                <div class="v8-hero-meta">
                    <span class="v8-live-pill">
                        <i></i> DATABASE CONNECTED
                    </span>
                    <span>REAL-TIME DATA</span>
                    <span>TQM PERFORMANCE</span>
                </div>
            </div>

            <div class="v8-hero-side">
                <div class="v8-date-label">REPORTING DATE</div>
                <div class="v8-date-value">
                    {date.today().strftime("%d %B %Y")}
                </div>
                <div class="v8-brand-mark">EH</div>
            </div>
        </section>
        """
    )

    if announcements:
        ann = announcements[0]
        badge_cls = (
            "ems-badge-urgent"
            if ann.priority == "Urgent"
            else ("ems-badge-important" if ann.priority == "Important" else "ems-badge-normal")
        )
        st.html(
            f"""
            <div class="ems-banner">
                <span class="ems-badge {badge_cls}">{safe_text(ann.priority)}</span>
                <div style="flex:1;">
                    <strong class="ems-banner-title" style="font-size:14px;">{safe_text(ann.title)}</strong>
                    <div class="ems-banner-content" style="font-size:13px; margin-top:2px;">{safe_text(ann.content)}</div>
                </div>
                <div class="ems-banner-author" style="font-size:11px;">Posted by {safe_text(ann.posted_by)}</div>
            </div>
            """
        )

    st.html(
        """
        <div class="v8-section-heading">
            <div>
                <span>WORKFORCE OVERVIEW</span>
                <h2>Key performance indicators</h2>
            </div>
            <div class="v8-section-status">
                LIVE
            </div>
        </div>
        """
    )

    kpi_columns = st.columns(
        4,
        gap="medium",
    )

    primary_kpis = [
        (
            "Total Employees",
            total,
            "Entire workforce",
            "users",
            "blue",
        ),
        (
            "Active Employees",
            active,
            f"{active_percentage:.1f}% of workforce",
            "user-check",
            "green",
        ),
        (
            "Inactive Employees",
            inactive,
            "Currently inactive",
            "user-off",
            "red",
        ),
        (
            "On Leave",
            on_leave,
            "Current leave status",
            "calendar",
            "orange",
        ),
    ]

    for column, item in zip(
        kpi_columns,
        primary_kpis,
    ):
        label, value, note, icon, tone = item

        with column:
            st.html(
                f"""
                <article class="v8-kpi v8-kpi-{tone}">
                    <div class="v8-kpi-top">
                        <span class="v8-kpi-icon">
                            {ui_icon(icon, 20)}
                        </span>
                        <span class="v8-kpi-label">
                            {safe_text(label)}
                        </span>
                    </div>

                    <div class="v8-kpi-value">
                        {safe_text(value)}
                    </div>

                    <div class="v8-kpi-note">
                        {safe_text(note)}
                    </div>
                </article>
                """
            )

    secondary = [
        (
            "New Joiners",
            new_joiners,
            "This month",
            "user-plus",
            "blue",
        ),
        (
            "Pending Leaves",
            pending_leaves,
            "Awaiting review",
            "calendar",
            "orange",
        ),
        (
            "Attendance Today",
            f"{attendance_summary['attendance_rate']}%",
            f"{attendance_summary['present_count']} of {attendance_summary['total_active_employees']} present",
            "activity",
            "green",
        ),
        (
            "Departments",
            department_count,
            "Organizational units",
            "building",
            "purple",
        ),
    ]

    secondary_columns = st.columns(
        4,
        gap="medium",
    )

    for column, item in zip(
        secondary_columns,
        secondary,
    ):
        label, value, note, icon, tone = item

        with column:
            st.html(
                f"""
                <article class="v8-mini-card">
                    <div class="v8-mini-icon v8-{tone}">
                        {ui_icon(icon, 18)}
                    </div>

                    <div class="v8-mini-body">
                        <span>{safe_text(label)}</span>
                        <strong>{safe_text(value)}</strong>
                        <small>{safe_text(note)}</small>
                    </div>
                </article>
                """
            )

    analytics_left, analytics_right = st.columns(
        [1.05, 0.95],
        gap="large",
    )

    active_width = active / total * 100 if total else 0
    inactive_width = inactive / total * 100 if total else 0
    leave_width = on_leave / total * 100 if total else 0

    with analytics_left:
        st.html(
            f"""
            <section class="v8-panel v8-health-panel">
                <div class="v8-panel-header">
                    <div>
                        <span class="v8-panel-eyebrow">
                            WORKFORCE HEALTH
                        </span>
                        <h2>Employee status</h2>
                        <p>Current workforce availability</p>
                    </div>

                    <span class="v8-panel-badge">
                        {active_percentage:.1f}% ACTIVE
                    </span>
                </div>

                <div class="v8-health-stats">
                    <div>
                        <strong>{active}</strong>
                        <span>Active</span>
                    </div>
                    <div>
                        <strong>{inactive}</strong>
                        <span>Inactive</span>
                    </div>
                    <div>
                        <strong>{on_leave}</strong>
                        <span>On Leave</span>
                    </div>
                </div>

                <div class="v8-health-track">
                    <span
                        class="v8-health-active"
                        style="width:{active_width:.2f}%"
                    ></span>
                    <span
                        class="v8-health-inactive"
                        style="width:{inactive_width:.2f}%"
                    ></span>
                    <span
                        class="v8-health-leave"
                        style="width:{leave_width:.2f}%"
                    ></span>
                </div>

                <div class="v8-legend">
                    <span>
                        <i class="active"></i>Active
                    </span>
                    <span>
                        <i class="inactive"></i>Inactive
                    </span>
                    <span>
                        <i class="leave"></i>On Leave
                    </span>
                </div>
            </section>
            """
        )

    with analytics_right:
        department_rows = ""

        max_department = max(
            (
                count
                for _, count in department_counts
            ),
            default=1,
        )

        for department, count in department_counts[:6]:
            width = count / max_department * 100

            department_rows += f"""
                <div class="v8-data-row">
                    <div class="v8-data-row-top">
                        <span>{safe_text(department)}</span>
                        <strong>{count}</strong>
                    </div>

                    <div class="v8-data-track">
                        <span style="width:{width:.2f}%"></span>
                    </div>
                </div>
            """

        if not department_rows:
            department_rows = """
                <div class="v8-empty">
                    No department data available.
                </div>
            """

        st.html(
            f"""
            <section class="v8-panel">
                <div class="v8-panel-header">
                    <div>
                        <span class="v8-panel-eyebrow">
                            ORGANIZATION
                        </span>
                        <h2>Department distribution</h2>
                        <p>
                            Workforce concentration by department
                        </p>
                    </div>

                    <span class="v8-panel-count">
                        {department_count} UNITS
                    </span>
                </div>

                <div class="v8-data-list">
                    {department_rows}
                </div>
            </section>
            """
        )

    designation_left, designation_right = st.columns(
        [1.05, 0.95],
        gap="large",
    )

    with designation_left:
        designation_rows = ""

        for designation, count in designation_counts[:6]:
            initials = safe_text(
                str(designation)[:2]
            ).upper()

            designation_rows += f"""
                <div class="v8-role-row">
                    <div class="v8-role-avatar">
                        {initials}
                    </div>

                    <div class="v8-role-info">
                        <strong>
                            {safe_text(designation)}
                        </strong>
                        <span>Employee designation</span>
                    </div>

                    <div class="v8-role-count">
                        {count}
                    </div>
                </div>
            """

        if not designation_rows:
            designation_rows = """
                <div class="v8-empty">
                    No designation data available.
                </div>
            """

        st.html(
            f"""
            <section class="v8-panel">
                <div class="v8-panel-header">
                    <div>
                        <span class="v8-panel-eyebrow">
                            TALENT STRUCTURE
                        </span>
                        <h2>Designation intelligence</h2>
                        <p>
                            Job-role distribution across the workforce
                        </p>
                    </div>

                    <span class="v8-panel-count">
                        {designation_count} ROLES
                    </span>
                </div>

                <div class="v8-role-list">
                    {designation_rows}
                </div>
            </section>
            """
        )

    with designation_right:
        st.html(
            """
            <section class="v8-panel v8-actions-panel">
                <div class="v8-panel-header">
                    <div>
                        <span class="v8-panel-eyebrow">
                            OPERATIONS
                        </span>
                        <h2>Quick actions</h2>
                        <p>Common HR operations</p>
                    </div>
                </div>
            </section>
            """
        )

        action_columns = st.columns(
            2,
            gap="small",
        )

        with action_columns[0]:
            if st.button(
                "Add Employee",
                key="v8_add_employee",
                icon=":material/person_add:",
                type="primary",
                width="stretch",
            ):
                navigate_to("Add Employee")

            if st.button(
                "Search Employees",
                key="v8_search_employee",
                icon=":material/search:",
                width="stretch",
            ):
                navigate_to("Search Employees")

        with action_columns[1]:
            if st.button(
                "Import CSV",
                key="v8_import_csv",
                icon=":material/upload_file:",
                width="stretch",
            ):
                navigate_to("CSV Import")

            if st.button(
                "Manage Employees",
                key="v8_manage_employee",
                icon=":material/manage_accounts:",
                width="stretch",
            ):
                navigate_to("Update / Delete")

    rows = ""

    for employee in recent_employees:
        full_name = (
            f"{employee.first_name} "
            f"{employee.last_name}"
        )

        status_label = employee.status.replace(
            "_",
            " ",
        ).title()

        status_class = {
            "active": "active",
            "inactive": "inactive",
            "on_leave": "leave",
        }.get(
            employee.status,
            "",
        )

        first_initial = safe_text(
            employee.first_name[:1].upper()
        )

        rows += f"""
            <tr>
                <td>
                    <span class="v8-employee-id">
                        {safe_text(employee.employee_id)}
                    </span>
                </td>

                <td>
                    <div class="v8-employee-cell">
                        <div class="v8-employee-avatar">
                            {first_initial}
                        </div>

                        <div>
                            <strong>
                                {safe_text(full_name)}
                            </strong>
                            <span>
                                {safe_text(employee.email)}
                            </span>
                        </div>
                    </div>
                </td>

                <td>
                    {safe_text(employee.department)}
                </td>

                <td>
                    {safe_text(employee.designation)}
                </td>

                <td>
                    <span class="v8-status {status_class}">
                        {safe_text(status_label)}
                    </span>
                </td>

                <td>
                    {safe_text(employee.joining_date)}
                </td>
            </tr>
        """

    if not rows:
        rows = """
            <tr>
                <td colspan="6">
                    <div class="v8-empty">
                        No employee records available.
                    </div>
                </td>
            </tr>
        """

    st.html(
        f"""
        <section class="v8-table-panel">
            <div class="v8-panel-header">
                <div>
                    <span class="v8-panel-eyebrow">
                        PEOPLE
                    </span>
                    <h2>Recent employees</h2>
                    <p>
                        Latest employee records created in the system
                    </p>
                </div>

                <span class="v8-panel-badge">
                    LIVE RECORDS
                </span>
            </div>

            <div class="v8-table-scroll">
                <table class="v8-table">
                    <thead>
                        <tr>
                            <th>EMPLOYEE ID</th>
                            <th>EMPLOYEE</th>
                            <th>DEPARTMENT</th>
                            <th>DESIGNATION</th>
                            <th>STATUS</th>
                            <th>JOINING DATE</th>
                        </tr>
                    </thead>

                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </section>
        """
    )

    st.html(
        """
        <footer class="v8-footer">
            <span>Employee Management System</span>
            <span>•</span>
            <span>Live operational dashboard</span>
            <span>•</span>
            <span>TQM performance monitored</span>
        </footer>
        """
    )


def add_employee_page() -> None:
    load_dashboard_styles()

    # Reset fields only after successful employee creation.
    # This runs before the widgets are created, avoiding Streamlit's
    # restriction on changing widget state after widget instantiation.
    if st.session_state.pop("reset_add_employee_form", False):
        st.session_state["add_employee_id"] = ""
        st.session_state["add_employee_first_name"] = ""
        st.session_state["add_employee_last_name"] = ""
        st.session_state["add_employee_email"] = ""
        st.session_state["add_employee_phone"] = ""
        st.session_state["add_employee_department"] = ""
        st.session_state["add_employee_designation"] = ""
        st.session_state["add_employee_joining_date"] = date.today()
        st.session_state["add_employee_salary"] = 0.01
        st.session_state["add_employee_status"] = "active"

    # Show the success message after the automatic rerun.
    success_message = st.session_state.pop(
        "add_employee_success_message",
        None,
    )
    if success_message:
        st.success(success_message, icon="✅")



    st.html(
        """
        <div class="page-heading">
            <div class="page-eyebrow">EMPLOYEE MANAGEMENT</div>
            <div class="page-title">Add Employee</div>
            <div class="page-subtitle">
                Create a new employee record in the live database.
            </div>
        </div>
        """
    )

    with st.form("add_employee_form"):
        col1, col2 = st.columns(2)

        with col1:
            employee_id = st.text_input(
                "Employee ID", key="add_employee_id"
            )
            first_name = st.text_input(
                "First Name", key="add_employee_first_name"
            )
            last_name = st.text_input(
                "Last Name", key="add_employee_last_name"
            )
            email = st.text_input(
                "Email", key="add_employee_email"
            )
            phone = st.text_input(
                "Phone", key="add_employee_phone"
            )

        with col2:
            department = st.text_input(
                "Department", key="add_employee_department"
            )
            designation = st.text_input(
                "Designation", key="add_employee_designation"
            )
            joining_date = st.date_input(
                "Joining Date",
                value=date.today(),
                key="add_employee_joining_date",
            )
            salary = st.number_input(
                "Salary",
                min_value=0.01,
                value=0.01,
                step=1000.0,
                key="add_employee_salary",
            )
            status = st.selectbox(
                "Status",
                ["active", "inactive", "on_leave"],
                key="add_employee_status",
            )

        submitted = st.form_submit_button(
            "Add Employee",
            type="primary",
            width="stretch",
        )

    if not submitted:
        return

    db = get_db()

    try:
        now = datetime.now()
        employee = Employee(
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            department=department,
            designation=designation,
            joining_date=joining_date,
            salary=Decimal(str(salary)),
            status=status,
            created_at=now,
            updated_at=now,
        )

        EmployeeService(db).create_employee(employee)

        # Save the message so it remains visible after the automatic rerun.
        st.session_state["add_employee_success_message"] = (
            f"Employee {employee_id} added successfully."
        )

        # Reset the form only after creation succeeds.
        st.session_state["reset_add_employee_form"] = True
        st.rerun()

    except ValueError as exc:
        # Validation failures preserve the user's entered values.
        st.error(str(exc))

    finally:
        db.close()

def employee_search_page() -> None:
    load_dashboard_styles()

    st.html(
        """
        <div class="page-heading">
            <div class="page-eyebrow">
                EMPLOYEE MANAGEMENT
            </div>
            <div class="page-title">
                Employee Search
            </div>
            <div class="page-subtitle">
                Search and filter real employee records.
            </div>
        </div>
        """
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        search_term = st.text_input(
            "Search",
            placeholder="ID, name, email, phone...",
        )

    with col2:
        department = st.text_input(
            "Department Filter"
        )

    with col3:
        status = st.selectbox(
            "Status Filter",
            [
                "All",
                "active",
                "inactive",
                "on_leave",
            ],
        )

    page_col, size_col = st.columns(2)

    with page_col:
        page = st.number_input(
            "Page",
            min_value=1,
            value=1,
            step=1,
        )

    with size_col:
        page_size = st.selectbox(
            "Records per page",
            [
                10,
                20,
                50,
                100,
            ],
            index=1,
        )

    db = get_db()

    try:
        employees = EmployeeService(
            db
        ).search_employees(
            search_term=search_term,
            department=department or None,
            status=None if status == "All" else status,
            page=int(page),
            page_size=page_size,
        )

        if employees:
            data = []

            for employee in employees:
                data.append(
                    {
                        "Employee ID": employee.employee_id,
                        "Name": (
                            f"{employee.first_name} "
                            f"{employee.last_name}"
                        ),
                        "Email": employee.email,
                        "Phone": employee.phone,
                        "Department": employee.department,
                        "Designation": employee.designation,
                        "Joining Date": str(
                            employee.joining_date
                        ),
                        "Salary": float(employee.salary),
                        "Status": employee.status,
                    }
                )

            st.dataframe(
                data,
                width="stretch",
                hide_index=True,
            )

        else:
            st.info("No employees found.")

    finally:
        db.close()


def manage_employee_page() -> None:
    load_dashboard_styles()

    st.html(
        """
        <div class="page-heading">
            <div class="page-eyebrow">
                EMPLOYEE MANAGEMENT
            </div>
            <div class="page-title">
                Update / Delete
            </div>
            <div class="page-subtitle">
                Safely manage an existing employee record.
            </div>
        </div>
        """
    )

    db_peek = get_db()
    all_emps = []
    try:
        all_emps = EmployeeService(db_peek).get_all_employees()
    finally:
        db_peek.close()

    emp_options = ["-- Select an Employee to Edit --"] + [
        f"{e.employee_id} - {e.first_name} {e.last_name} ({e.department})"
        for e in all_emps
    ]

    col_pick, col_type = st.columns([1.5, 1])
    with col_pick:
        chosen_option = st.selectbox("Choose Existing Employee", emp_options, key="manage_emp_select")
    with col_type:
        typed_id = st.text_input("Or Enter Employee ID manually", placeholder="e.g. emp001", key="manage_emp_input")

    employee_id = ""
    if chosen_option and not chosen_option.startswith("--"):
        employee_id = chosen_option.split(" - ")[0].strip()
    elif typed_id:
        employee_id = typed_id.strip()

    if not employee_id:
        st.info("Select an employee from the dropdown or type an Employee ID above to view and update details.")
        return

    db = get_db()

    try:
        service = EmployeeService(db)

        employee = service.get_employee_by_id(
            employee_id
        )

        if employee is None:
            st.warning("Employee not found.")
            return

        st.write(
            f"**Current Employee:** "
            f"{employee.first_name} "
            f"{employee.last_name}"
        )

        with st.form("update_employee_form"):
            first_name = st.text_input(
                "First Name",
                value=employee.first_name,
            )

            last_name = st.text_input(
                "Last Name",
                value=employee.last_name,
            )

            email = st.text_input(
                "Email",
                value=employee.email,
            )

            phone = st.text_input(
                "Phone",
                value=employee.phone,
            )

            department = st.text_input(
                "Department",
                value=employee.department,
            )

            designation = st.text_input(
                "Designation",
                value=employee.designation,
            )

            joining_date = st.date_input(
                "Joining Date",
                value=employee.joining_date,
            )

            salary = st.number_input(
                "Salary",
                min_value=0.01,
                value=float(employee.salary),
                step=1000.0,
            )

            status = st.selectbox(
                "Status",
                [
                    "active",
                    "inactive",
                    "on_leave",
                ],
                index=[
                    "active",
                    "inactive",
                    "on_leave",
                ].index(employee.status),
            )

            update_clicked = st.form_submit_button(
                "Update Employee",
                type="primary",
                width="stretch",
            )

        if update_clicked:
            try:
                service.update_employee(
                    employee_id,
                    {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                        "department": department,
                        "designation": designation,
                        "joining_date": joining_date,
                        "salary": Decimal(str(salary)),
                        "status": status,
                    },
                )

                st.success(
                    "Employee updated successfully."
                )

            except ValueError as exc:
                st.error(str(exc))

        st.divider()

        if st.button(
            "Delete Employee",
            type="secondary",
            width="stretch",
        ):
            try:
                service.delete_employee(
                    employee_id
                )

                st.success(
                    "Employee deleted successfully."
                )

                st.rerun()

            except ValueError as exc:
                st.error(str(exc))

    finally:
        db.close()


def csv_import_page() -> None:
    load_dashboard_styles()

    st.html(
        """
        <div class="page-heading">
            <div class="page-eyebrow">
                DATA OPERATIONS
            </div>
            <div class="page-title">
                CSV Import
            </div>
            <div class="page-subtitle">
                Import validated real employee records in bulk.
            </div>
        </div>
        """
    )

    st.info(
        "Upload a CSV containing real employee records. "
        "Ensure headers match the required specification."
    )

    sample_csv = "employee_id,first_name,last_name,email,phone,department,designation,joining_date,salary,status\nEMP101,John,Doe,john.doe@example.com,9876543210,Engineering,Software Engineer,2024-01-15,75000,active\nEMP102,Sarah,Connor,sarah.c@example.com,9876543211,Human Resources,HR Specialist,2023-06-01,65000,active"
    st.download_button(
        label="📥 Download Sample CSV Template",
        data=sample_csv,
        file_name="employee_import_template.csv",
        mime="text/csv",
    )

    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=["csv"],
    )

    if uploaded_file is None:
        return

    if st.button(
        "Import Employees",
        type="primary",
        width="stretch",
    ):
        temp_path = "data/uploaded_employee_import.csv"

        with open(
            temp_path,
            "wb",
        ) as file:
            file.write(
                uploaded_file.getbuffer()
            )

        db = get_db()

        try:
            result = CSVImportService(
                db
            ).import_csv(
                temp_path
            )

            st.success(
                f"Import completed. "
                f"Successful: {result['successful']}"
            )

            st.write(
                f"Duplicates: {result['duplicates']}"
            )

            st.write(
                f"Invalid: {result['invalid']}"
            )

            st.write(
                f"Failed: {result['failed']}"
            )

            if result["errors"]:
                st.subheader("Import Errors")
                st.json(result["errors"])

        except (
            ValueError,
            FileNotFoundError,
        ) as exc:
            st.error(str(exc))

        finally:
            db.close()


def user_management_page() -> None:
    load_dashboard_styles()

    st.html(
        """
        <div class="page-heading">
            <div class="page-eyebrow">
                SYSTEM ADMINISTRATION
            </div>
            <div class="page-title">
                User Management
            </div>
            <div class="page-subtitle">
                Create real HR and Employee login accounts and
                securely manage credentials linked to real users.
            </div>
        </div>
        """
    )

    st.info(
        "Only real user accounts should be managed here. "
        "No sample or test users are created automatically."
    )

    db = get_db()

    try:
        users = list(
            db.scalars(
                select(User).order_by(User.id)
            ).all()
        )

        st.subheader("Existing Users")

        if users:
            user_rows = []

            for user in users:
                linked_employee = None

                if user.employee_id is not None:
                    linked_employee = db.get(
                        Employee,
                        user.employee_id,
                    )

                user_rows.append(
                    {
                        "Username": user.username,
                        "Email": user.email,
                        "Role": user.role,
                        "Active": user.is_active,
                        "Employee ID": (
                            linked_employee.employee_id
                            if linked_employee
                            else "Not linked"
                        ),
                    }
                )

            st.dataframe(
                user_rows,
                width="stretch",
                hide_index=True,
            )

        else:
            st.info("No users found.")

        st.divider()

        st.subheader("Reset User Password")

        st.warning(
            "Password reset changes only the selected user's login "
            "credential. Employee profile data is not modified."
        )

        resettable_users = [
            user
            for user in users
            if user.id != st.session_state.get("user_id")
        ]

        if resettable_users:
            reset_options = {
                (
                    f"{user.username} | "
                    f"{user.email} | "
                    f"{user.role}"
                ): user.id
                for user in resettable_users
            }

            with st.form("reset_user_password_form"):
                selected_reset_label = st.selectbox(
                    "Select User",
                    list(reset_options.keys()),
                )

                new_password = st.text_input(
                    "New Password",
                    type="password",
                    placeholder="Enter new password",
                )

                confirm_password = st.text_input(
                    "Confirm New Password",
                    type="password",
                    placeholder="Re-enter new password",
                )

                reset_confirmed = st.checkbox(
                    "I confirm that I want to reset this user's password.",
                )

                reset_clicked = st.form_submit_button(
                    "Reset Password",
                    type="primary",
                    width="stretch",
                )

            if reset_clicked:
                selected_user_id = reset_options.get(
                    selected_reset_label
                )

                if selected_user_id is None:
                    st.error("Please select a valid user.")
                    return

                if not new_password:
                    st.error("New password is required.")
                    return

                if len(new_password) < 8:
                    st.error(
                        "Password must contain at least 8 characters."
                    )
                    return

                if new_password != confirm_password:
                    st.error(
                        "New password and confirmation do not match."
                    )
                    return

                if not reset_confirmed:
                    st.error(
                        "Please confirm the password reset."
                    )
                    return

                target_user = db.get(
                    User,
                    selected_user_id,
                )

                if target_user is None:
                    st.error("Selected user no longer exists.")
                    return

                if target_user.id == st.session_state.get("user_id"):
                    st.error(
                        "For security, the currently logged-in "
                        "admin account cannot be reset from this screen."
                    )
                    return

                try:
                    target_user.password_hash = bcrypt.hashpw(
                        new_password.encode("utf-8"),
                        bcrypt.gensalt(),
                    ).decode("utf-8")

                    target_user.updated_at = datetime.now()

                    db.commit()

                    st.success(
                        f"Password reset successfully for "
                        f"'{target_user.username}'."
                    )

                except Exception:
                    db.rollback()
                    st.error(
                        "Password reset failed. "
                        "No credential changes were saved."
                    )

        else:
            st.info(
                "No other user account is currently available "
                "for password reset."
            )

        st.divider()

        st.subheader("Create User Account")

        with st.form("create_user_form"):
            username = st.text_input(
                "Username",
                placeholder="Enter real username",
            )

            email = st.text_input(
                "Email",
                placeholder="Enter real email address",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter initial password",
            )

            role = st.selectbox(
                "Role",
                [
                    "hr",
                    "employee",
                ],
            )

            employees = list(
                db.scalars(
                    select(Employee).order_by(
                        Employee.employee_id
                    )
                ).all()
            )

            employee_options = {
                "No employee link": None
            }

            for employee in employees:
                employee_options[
                    (
                        f"{employee.employee_id} | "
                        f"{employee.first_name} "
                        f"{employee.last_name} | "
                        f"{employee.email}"
                    )
                ] = employee.id

            selected_employee_label = st.selectbox(
                "Employee Mapping",
                list(employee_options.keys()),
                disabled=(role == "hr"),
                help=(
                    "Employee role must be linked to the "
                    "correct real employee record."
                ),
            )

            create_clicked = st.form_submit_button(
                "Create User",
                type="primary",
                width="stretch",
            )

        if create_clicked:
            username = username.strip()
            email = email.strip()

            if not username:
                st.error("Username is required.")
                return

            if not email:
                st.error("Email is required.")
                return

            if not password:
                st.error("Password is required.")
                return

            if len(password) < 8:
                st.error(
                    "Password must contain at least 8 characters."
                )
                return

            existing_username = db.scalar(
                select(User).where(
                    User.username == username
                )
            )

            if existing_username is not None:
                st.error(
                    "Username already exists."
                )
                return

            existing_email = db.scalar(
                select(User).where(
                    User.email == email
                )
            )

            if existing_email is not None:
                st.error(
                    "Email already exists."
                )
                return

            employee_id = None

            if role == "employee":
                employee_id = employee_options.get(
                    selected_employee_label
                )

                if employee_id is None:
                    st.error(
                        "An Employee account must be linked "
                        "to a real employee record."
                    )
                    return

                existing_mapping = db.scalar(
                    select(User).where(
                        User.employee_id == employee_id
                    )
                )

                if existing_mapping is not None:
                    st.error(
                        "This employee is already linked "
                        "to a user account."
                    )
                    return

            password_hash = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("utf-8")

            now = datetime.now()

            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                employee_id=employee_id,
                is_active=True,
                created_at=now,
                updated_at=now,
            )

            try:
                db.add(user)
                db.commit()

                st.success(
                    f"User '{username}' created successfully."
                )

                st.rerun()

            except Exception as exc:
                db.rollback()
                st.error(
                    f"User creation failed: {exc}"
                )

    finally:
        db.close()


def activity_log_page() -> None:
    st.title("Activity Log")
    st.caption(
        "Review recent administrative activities and their timestamps."
    )

    db = get_db()

    try:
        recent_logs = AuditLogService.get_recent_logs(
            db,
            limit=500,
        )

        actions = sorted(
            {log.action for log in recent_logs}
        )

        filter_options = ["All Actions"] + actions

        selected_action = st.selectbox(
            "Filter by action",
            filter_options,
        )

        if selected_action == "All Actions":
            logs = recent_logs
        else:
            logs = AuditLogService.get_recent_logs(
                db,
                limit=500,
                action=selected_action,
            )

        if not logs:
            st.info(
                "No audit activities found yet. "
                "Activities will appear after logging is integrated."
            )
            return

        rows = [
            {
                "Timestamp": (
                    log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    if log.created_at
                    else ""
                ),
                "Username": log.actor_username,
                "Action": log.action,
                "Entity Type": log.entity_type,
                "Entity ID": log.entity_id or "",
                "Details": log.details or "",
            }
            for log in logs
        ]

        st.dataframe(
            rows,
            width="stretch",
            hide_index=True,
        )

        st.caption(f"Showing {len(rows)} audit records.")

    except Exception:
        st.error(
            "Activity logs could not be loaded. "
            "Please check the application logs."
        )

    finally:
        db.close()


def leave_management_page() -> None:
    load_dashboard_styles()

    st.html(
        """
        <div class="page-heading">
            <div class="page-eyebrow">WORKFORCE OPERATIONS</div>
            <div class="page-title">Leave Operations & Approvals</div>
            <div class="page-subtitle">
                Review employee time-off requests, approve or decline with feedback, and maintain workforce availability schedules.
            </div>
        </div>
        """
    )

    db = get_db()
    try:
        leave_service = LeaveService(db)
        employee_service = EmployeeService(db)

        pending_count = leave_service.count_pending()
        on_leave_today = leave_service.count_on_leave_today()
        all_leaves = leave_service.get_all_leaves(limit=200)

        approved_count = sum(1 for l in all_leaves if l.status == "Approved")
        rejected_count = sum(1 for l in all_leaves if l.status == "Rejected")

        # KPI metric chips
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.html(
                f"""
                <div class="ems-stat-chip">
                    <span style="color:#b45309; font-size:12px; font-weight:700;">PENDING REVIEW</span>
                    <strong>{pending_count}</strong>
                </div>
                """
            )
        with m2:
            st.html(
                f"""
                <div class="ems-stat-chip">
                    <span style="color:#047857; font-size:12px; font-weight:700;">ON LEAVE TODAY</span>
                    <strong>{on_leave_today}</strong>
                </div>
                """
            )
        with m3:
            st.html(
                f"""
                <div class="ems-stat-chip">
                    <span style="color:#1d4ed8; font-size:12px; font-weight:700;">TOTAL APPROVED</span>
                    <strong>{approved_count}</strong>
                </div>
                """
            )
        with m4:
            st.html(
                f"""
                <div class="ems-stat-chip">
                    <span style="color:#b91c1c; font-size:12px; font-weight:700;">TOTAL DECLINED</span>
                    <strong>{rejected_count}</strong>
                </div>
                """
            )

        st.write("")
        st.write("")

        # Filter bar
        f_col1, f_col2 = st.columns([1, 1])
        with f_col1:
            status_filter = st.selectbox(
                "Filter by Request Status",
                ["All", "Pending", "Approved", "Rejected"],
                index=0,
                key="admin_leave_status_filter",
            )
        with f_col2:
            employees = employee_service.get_all_employees()
            departments = sorted(list({e.department for e in employees if e.department}))
            dept_filter = st.selectbox(
                "Filter by Department",
                ["All"] + departments,
                index=0,
                key="admin_leave_dept_filter",
            )

        filtered_leaves = leave_service.get_all_leaves(
            status=status_filter if status_filter != "All" else None,
            department=dept_filter if dept_filter != "All" else None,
            limit=200,
        )

        if not filtered_leaves:
            st.info("No leave requests found matching the selected filter criteria.")
            return

        st.subheader(f"Requests ({len(filtered_leaves)})")

        for l in filtered_leaves:
            emp = l.employee
            badge_class = (
                "ems-badge-pending"
                if l.status == "Pending"
                else ("ems-badge-approved" if l.status == "Approved" else "ems-badge-rejected")
            )

            emp_name = f"{emp.first_name} {emp.last_name}" if emp else "Unknown Employee"
            emp_id = emp.employee_id if emp else "N/A"
            dept = emp.department if emp else "N/A"

            with st.container(border=True):
                top_col1, top_col2 = st.columns([3, 1])
                with top_col1:
                    st.markdown(f"### {safe_text(emp_name)} `({safe_text(emp_id)})` • {safe_text(dept)}")
                    st.caption(
                        f"📅 **{safe_text(l.leave_type)}** | {l.start_date.strftime('%d %b %Y')} to {l.end_date.strftime('%d %b %Y')} "
                        f"({l.days_count} {'day' if l.days_count == 1 else 'days'}) • Applied on {l.applied_at.strftime('%d %b %Y, %I:%M %p')}"
                    )
                with top_col2:
                    st.html(f"<div style='text-align:right;'><span class='ems-badge {badge_class}'>{safe_text(l.status)}</span></div>")

                st.markdown(f"**Reason:** *\"{safe_text(l.reason)}\"*")

                if l.status == "Pending":
                    st.divider()
                    st.markdown("**Take Action on Request:**")
                    with st.form(f"leave_action_form_{l.id}"):
                        remarks = st.text_input(
                            "Manager / Admin Remarks (Optional)",
                            key=f"remarks_{l.id}",
                            placeholder="Add reason or note for employee...",
                        )
                        btn_c1, btn_c2, _ = st.columns([1, 1, 3])
                        with btn_c1:
                            approve_btn = st.form_submit_button("✅ Approve Leave", type="primary", width="stretch")
                        with btn_c2:
                            reject_btn = st.form_submit_button("❌ Decline Leave", type="secondary", width="stretch")

                        if approve_btn:
                            leave_service.review_leave(
                                leave_id=l.id,
                                status="Approved",
                                admin_remarks=remarks,
                                actor_username=st.session_state.get("username", "Admin"),
                            )
                            st.success(f"Leave request for {emp_name} has been approved.")
                            st.rerun()

                        if reject_btn:
                            leave_service.review_leave(
                                leave_id=l.id,
                                status="Rejected",
                                admin_remarks=remarks,
                                actor_username=st.session_state.get("username", "Admin"),
                            )
                            st.warning(f"Leave request for {emp_name} has been declined.")
                            st.rerun()
                else:
                    if l.admin_remarks:
                        st.caption(f"**Remarks:** {safe_text(l.admin_remarks)}")
                    if l.reviewed_at:
                        st.caption(f"Reviewed at: {l.reviewed_at.strftime('%d %b %Y, %I:%M %p')}")

    finally:
        db.close()


def attendance_tracker_page() -> None:
    load_dashboard_styles()

    st.html(
        """
        <div class="page-heading">
            <div class="page-eyebrow">WORKFORCE TIME & ATTENDANCE</div>
            <div class="page-title">Daily Attendance Tracker</div>
            <div class="page-subtitle">
                Monitor team check-in status, clock-out intervals, late entries, and generate verified attendance records.
            </div>
        </div>
        """
    )

    db = get_db()
    try:
        attendance_service = AttendanceService(db)
        employee_service = EmployeeService(db)

        col_date, col_actions = st.columns([1, 2])
        with col_date:
            selected_date = st.date_input(
                "Select Attendance Date",
                value=date.today(),
                key="admin_attendance_date",
            )

        summary = attendance_service.get_daily_summary(selected_date)

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.html(
                f"""
                <div class="ems-stat-chip">
                    <span style="color:#2563eb; font-size:12px; font-weight:700;">TOTAL ACTIVE</span>
                    <strong>{summary['total_active_employees']}</strong>
                </div>
                """
            )
        with m2:
            st.html(
                f"""
                <div class="ems-stat-chip">
                    <span style="color:#047857; font-size:12px; font-weight:700;">PRESENT TODAY</span>
                    <strong>{summary['present_count']}</strong>
                </div>
                """
            )
        with m3:
            st.html(
                f"""
                <div class="ems-stat-chip">
                    <span style="color:#d97706; font-size:12px; font-weight:700;">LATE ENTRIES</span>
                    <strong>{summary['late_count']}</strong>
                </div>
                """
            )
        with m4:
            st.html(
                f"""
                <div class="ems-stat-chip">
                    <span style="color:#b91c1c; font-size:12px; font-weight:700;">ABSENT / UNLOGGED</span>
                    <strong>{summary['absent_count']}</strong>
                </div>
                """
            )
        with m5:
            st.html(
                f"""
                <div class="ems-stat-chip">
                    <span style="color:#7c3aed; font-size:12px; font-weight:700;">ATTENDANCE RATE</span>
                    <strong>{summary['attendance_rate']}%</strong>
                </div>
                """
            )

        st.write("")
        tab_log, tab_manual = st.tabs(["📋 Attendance Records", "✏️ Manual Punch Override"])

        with tab_log:
            records = summary["records"]
            if not records:
                st.info(f"No punch records found for {selected_date.strftime('%d %B %Y')}.")
            else:
                table_rows = []
                for r in records:
                    e = r.employee
                    table_rows.append(
                        {
                            "Employee ID": e.employee_id if e else "N/A",
                            "Name": f"{e.first_name} {e.last_name}" if e else "N/A",
                            "Department": e.department if e else "N/A",
                            "Clock In": r.clock_in.strftime("%I:%M:%S %p") if r.clock_in else "Not Recorded",
                            "Clock Out": r.clock_out.strftime("%I:%M:%S %p") if r.clock_out else "Active Shift",
                            "Hours": f"{r.work_hours:.2f} hrs",
                            "Status": r.status,
                            "Notes": r.notes or "-",
                        }
                    )

                st.dataframe(
                    table_rows,
                    width="stretch",
                    hide_index=True,
                )

                # Export CSV
                import io
                import csv
                output = io.StringIO()
                if table_rows:
                    writer = csv.DictWriter(output, fieldnames=table_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(table_rows)

                st.download_button(
                    label="📥 Export Attendance CSV",
                    data=output.getvalue(),
                    file_name=f"attendance_{selected_date}.csv",
                    mime="text/csv",
                )

        with tab_manual:
            st.markdown("Record or correct attendance for employees who worked offsite or missed punch:")
            employees = employee_service.get_all_employees()
            emp_map = {f"{e.first_name} {e.last_name} ({e.employee_id})": e for e in employees}

            with st.form("manual_attendance_form"):
                sel_name = st.selectbox("Select Employee", list(emp_map.keys()))
                c1, c2, c3 = st.columns(3)
                with c1:
                    status_choice = st.selectbox("Status", ["Present", "Late", "Half Day", "On Leave"])
                with c2:
                    clock_in_time = st.time_input("Clock In Time", value=datetime.strptime("09:00:00", "%H:%M:%S").time())
                with c3:
                    clock_out_time = st.time_input("Clock Out Time", value=datetime.strptime("17:30:00", "%H:%M:%S").time())

                notes = st.text_input("Operational Notes / Approval Justification")
                submit_manual = st.form_submit_button("Record Verified Attendance", type="primary")

                if submit_manual:
                    target_emp = emp_map[sel_name]
                    cin = datetime.combine(selected_date, clock_in_time)
                    cout = datetime.combine(selected_date, clock_out_time)

                    rec = attendance_service.repository.get_by_employee_and_date(target_emp.id, selected_date)
                    if not rec:
                        rec = attendance_service.repository.clock_in(target_emp.id, selected_date, cin, notes)
                    rec = attendance_service.repository.clock_out(target_emp.id, selected_date, cout)
                    rec.status = status_choice
                    if notes:
                        rec.notes = notes
                    db.commit()

                    st.success(f"Attendance recorded for {sel_name} on {selected_date}.")
                    st.rerun()

    finally:
        db.close()


def announcements_page() -> None:
    load_dashboard_styles()

    st.html(
        """
        <div class="page-heading">
            <div class="page-eyebrow">COMMUNICATIONS & ALERTS</div>
            <div class="page-title">Company Notice Board</div>
            <div class="page-subtitle">
                Publish company-wide announcements, policy directives, and priority workplace alerts.
            </div>
        </div>
        """
    )

    db = get_db()
    try:
        ann_service = AnnouncementService(db)

        tab_list, tab_create = st.tabs(["📢 Company Bulletins", "✍️ Post New Notice"])

        with tab_list:
            all_ann = ann_service.get_all()
            if not all_ann:
                st.info("No notices published yet.")
            else:
                for a in all_ann:
                    tone = (
                        "urgent"
                        if a.priority == "Urgent"
                        else ("important" if a.priority == "Important" else "normal")
                    )
                    status_label = "ACTIVE" if a.is_active else "INACTIVE / ARCHIVED"

                    with st.container(border=True):
                        h_col1, h_col2 = st.columns([3, 1])
                        with h_col1:
                            st.markdown(f"### {safe_text(a.title)}")
                            st.caption(
                                f"Posted by **{safe_text(a.posted_by)}** on {a.created_at.strftime('%d %B %Y at %I:%M %p')} • Target Audience: `{a.target_role.upper()}`"
                            )
                        with h_col2:
                            st.html(
                                f"""
                                <div style="text-align:right;">
                                    <span class="ems-badge ems-badge-{tone}">{safe_text(a.priority)}</span>
                                    <span style="font-size:11px; color:#64748b; margin-left:8px;">{status_label}</span>
                                </div>
                                """
                            )

                        st.markdown(a.content)
                        st.divider()

                        b_c1, b_c2, _ = st.columns([1, 1, 3])
                        with b_c1:
                            toggle_label = "Deactivate" if a.is_active else "Activate"
                            if st.button(toggle_label, key=f"toggle_ann_{a.id}", width="stretch"):
                                ann_service.toggle_status(
                                    a.id,
                                    not a.is_active,
                                    actor_username=st.session_state.get("username", "Admin"),
                                )
                                st.rerun()
                        with b_c2:
                            if st.button("Delete", key=f"del_ann_{a.id}", type="secondary", width="stretch"):
                                ann_service.delete(
                                    a.id,
                                    actor_username=st.session_state.get("username", "Admin"),
                                )
                                st.success("Notice deleted.")
                                st.rerun()

        with tab_create:
            with st.form("new_announcement_form"):
                title = st.text_input("Notice Title", placeholder="e.g. Q4 All-Hands Town Hall Meeting")
                c1, c2 = st.columns(2)
                with c1:
                    priority = st.selectbox("Priority Level", ["Normal", "Important", "Urgent"])
                with c2:
                    target_role = st.selectbox(
                        "Target Audience",
                        ["all", "employee", "hr"],
                        format_func=lambda r: "All Workforce" if r == "all" else ("Employees Only" if r == "employee" else "HR Team Only"),
                    )

                content = st.text_area(
                    "Announcement Body",
                    height=130,
                    placeholder="Provide full announcement details, schedules, links or instructions...",
                )

                submit_ann = st.form_submit_button("📢 Publish Announcement", type="primary")

                if submit_ann:
                    try:
                        ann_service.create_announcement(
                            title=title,
                            content=content,
                            priority=priority,
                            target_role=target_role,
                            posted_by=st.session_state.get("username", "Admin"),
                        )
                        st.success(f"Announcement '{title}' published successfully.")
                        st.rerun()
                    except ValueError as ve:
                        st.error(str(ve))

    finally:
        db.close()


def payslip_generator_page() -> None:
    load_dashboard_styles()

    st.html(
        """
        <div class="page-heading">
            <div class="page-eyebrow">COMPENSATION & PAYROLL</div>
            <div class="page-title">Official Payslip Generator</div>
            <div class="page-subtitle">
                Generate authenticated, print-ready employee salary slips with compliant earnings breakdown and tax deductions.
            </div>
        </div>
        """
    )

    db = get_db()
    try:
        employee_service = EmployeeService(db)
        employees = employee_service.get_all_employees()

        if not employees:
            st.info("No employees found in the system.")
            return

        emp_map = {f"{e.first_name} {e.last_name} ({e.employee_id})": e for e in employees}

        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            selected_name = st.selectbox("Select Employee", list(emp_map.keys()), key="admin_payslip_emp")
        with c2:
            current_month = date.today().month
            selected_month = st.selectbox(
                "Pay Month",
                range(1, 13),
                index=current_month - 1,
                format_func=lambda m: date(2026, m, 1).strftime("%B"),
                key="admin_payslip_month",
            )
        with c3:
            current_year = date.today().year
            selected_year = st.number_input("Pay Year", min_value=2020, max_value=2030, value=current_year, key="admin_payslip_year")

        emp = emp_map[selected_name]
        data = PayslipService.calculate_salary_breakdown(emp, int(selected_year), int(selected_month))
        html_content = PayslipService.generate_html_payslip(emp, int(selected_year), int(selected_month))

        # Preview card
        with st.container(border=True):
            st.markdown(f"### {emp.first_name} {emp.last_name} • {data['pay_period']}")
            st.caption(f"**ID:** {emp.employee_id} | **Dept:** {emp.department} | **Designation:** {emp.designation} | **Email:** {emp.email}")

            col_earn, col_ded = st.columns(2)
            with col_earn:
                st.markdown("#### 🟢 Earnings")
                for k, v in data["earnings"].items():
                    st.markdown(f"- **{k}:** ₹{v:,.2f}")
                st.markdown(f"**Total Gross Earnings:** `₹{data['total_earnings']:,.2f}`")

            with col_ded:
                st.markdown("#### 🔴 Deductions")
                for k, v in data["deductions"].items():
                    st.markdown(f"- **{k}:** ₹{v:,.2f}")
                st.markdown(f"**Total Deductions:** `₹{data['total_deductions']:,.2f}`")

            st.divider()
            st.html(
                f"""
                <div style="background:linear-gradient(135deg,#1e3a8a,#2563eb); color:#ffffff; padding:18px 24px; border-radius:12px; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-size:12px; opacity:0.85; text-transform:uppercase; letter-spacing:1px;">Net Payable Salary</div>
                        <div style="font-size:11px; opacity:0.75;">(Direct Bank Transfer / Account Credit)</div>
                    </div>
                    <div style="font-size:30px; font-weight:800;">₹{data['net_salary']:,.2f}</div>
                </div>
                """
            )

            st.write("")
            st.download_button(
                label="📥 Download Official Printable Payslip (HTML)",
                data=html_content,
                file_name=f"payslip_{emp.employee_id}_{selected_month}_{selected_year}.html",
                mime="text/html",
                type="primary",
            )

            with st.expander("📄 View Payslip Live Document Preview"):
                st.components.v1.html(html_content, height=650, scrolling=True)

    finally:
        db.close()


def main() -> None:
    # Defense-in-depth:
    # This dashboard must only be accessible to Admin.
    if st.session_state.get("role") != "admin":
        st.error("Access denied. Admin access is required.")
        return

    load_dashboard_styles()

    selected_page = render_sidebar()

    if selected_page == "Dashboard":
        dashboard_page()

    elif selected_page == "Add Employee":
        add_employee_page()

    elif selected_page == "Search Employees":
        employee_search_page()

    elif selected_page == "Update / Delete":
        manage_employee_page()

    elif selected_page == "Leave Management":
        leave_management_page()

    elif selected_page == "Attendance Tracker":
        attendance_tracker_page()

    elif selected_page == "Notice Board":
        announcements_page()

    elif selected_page == "Payslip Generator":
        payslip_generator_page()

    elif selected_page == "CSV Import":
        csv_import_page()

    elif selected_page == "User Management":
        user_management_page()

    elif selected_page == "Activity Log":
        activity_log_page()



if __name__ == "__main__":
    main()



