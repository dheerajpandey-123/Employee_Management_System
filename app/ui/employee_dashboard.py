from datetime import date, datetime
from html import escape
import csv
import io
import json
import zipfile

import streamlit as st

from app.database import SessionLocal
from app.models import Employee, User
from app.services.leave_service import LeaveService
from app.services.attendance_service import AttendanceService
from app.services.announcement_service import AnnouncementService
from app.services.payslip_service import PayslipService


# ============================================================
# SESSION MANAGEMENT
# ============================================================

def clear_employee_session() -> None:
    """
    Clear the authenticated session completely.

    This function only changes Streamlit session state.
    It does not modify any database record.
    """
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["username"] = None
    st.session_state["role"] = None


def logout() -> None:
    """Logout the current employee and return to login."""
    clear_employee_session()
    st.rerun()


def terminate_invalid_session(message: str) -> None:
    """
    Safely terminate an invalid employee session.

    No database changes are performed.
    """
    clear_employee_session()

    st.error(message)

    st.info("Please log in again to continue.")

    st.rerun()


# ============================================================
# TEXT / DISPLAY HELPERS
# ============================================================

def safe_text(
    value: object,
    fallback: str = "Not available",
) -> str:
    """Return escaped, display-safe text."""
    if value is None:
        return fallback

    text = str(value).strip()

    if not text:
        return fallback

    return escape(text)


def raw_text(
    value: object,
    fallback: str = "",
) -> str:
    """Return normalized text without HTML escaping."""
    if value is None:
        return fallback

    text = str(value).strip()

    return text if text else fallback


def full_name(employee: Employee) -> str:
    """Build employee full name from the real employee record."""
    first_name = raw_text(employee.first_name)
    last_name = raw_text(employee.last_name)

    name = f"{first_name} {last_name}".strip()

    return name or "Employee"


def initials(employee: Employee) -> str:
    """Generate initials from the employee's real name."""
    name = full_name(employee)
    parts = name.split()

    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()

    if parts:
        return parts[0][:2].upper()

    return "EM"


def icon_svg(
    name: str,
    size: int = 18,
    stroke_width: float = 1.9,
) -> str:
    """Return a consistent inline SVG icon for the dashboard UI."""
    paths = {
        "id": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 9h4M7 13h6M16.5 10.5h.01M16.5 14h.01"/>',
        "tenure": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        "department": '<rect x="4" y="4" width="16" height="17" rx="2"/><path d="M9 21V8h6v13M8 12h1M8 16h1M15 12h1M15 16h1"/>',
        "designation": '<path d="M9 6V4.8A1.8 1.8 0 0 1 10.8 3h2.4A1.8 1.8 0 0 1 15 4.8V6"/><rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 11h18M10 11v2h4v-2"/>',
        "attendance": '<path d="M7 3v3M17 3v3M4 9h16"/><rect x="4" y="5" width="16" height="16" rx="2"/><path d="m8 15 2.2 2.2L16 11.5"/>',
        "leave": '<path d="M7 3v3M17 3v3M4 9h16"/><rect x="4" y="5" width="16" height="16" rx="2"/><path d="M9 14h6M12 11v6"/>',
        "request": '<path d="M7 3h8l3 3v15H7z"/><path d="M15 3v4h4M9 12h6M9 16h5"/>',
        "profile": '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c.7-3.4 3.2-5 7-5s6.3 1.6 7 5"/>',
        "shield": '<path d="M12 3 20 6v5c0 5-3.4 8.3-8 10-4.6-1.7-8-5-8-10V6z"/><path d="m9 12 2 2 4-4"/>',
        "logout": '<path d="M10 5H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4"/><path d="m14 8 4 4-4 4M10 12h8"/>',
        "lock": '<rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
        "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
        "phone": '<path d="M7 4h3l1.5 4-2 1.5a15 15 0 0 0 5 5l1.5-2 4 1.5v3A2 2 0 0 1 18 19C10.8 18.5 5.5 13.2 5 6a2 2 0 0 1 2-2Z"/>',
        "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18"/>',
        "briefcase": '<rect x="3" y="6" width="18" height="14" rx="2"/><path d="M9 6V4h6v2M3 12h18M10 12v2h4v-2"/>',
        "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    }
    body = paths.get(name, paths["info"])
    return (
        f'<svg class="ui-icon" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>'
    )


def format_status(status: object) -> str:
    """Format employee status for display."""
    value = raw_text(status, "Unknown")

    return value.replace("_", " ").title()


def status_class(status: object) -> str:
    """Return semantic CSS status class."""
    normalized = raw_text(status).lower()

    if normalized == "active":
        return "active"

    if normalized == "inactive":
        return "inactive"

    if normalized in {"on_leave", "leave"}:
        return "leave"

    return "neutral"


def format_date(value: date | None) -> str:
    """Format a database date."""
    if value is None:
        return "Not available"

    return value.strftime("%d %b %Y")


def format_datetime(value: datetime | None) -> str:
    """Format a database datetime."""
    if value is None:
        return "Not available"

    return value.strftime("%d %b %Y, %I:%M %p")


# ============================================================
# EMPLOYMENT CALCULATIONS
# ============================================================

def calculate_tenure(joining_date: date | None) -> str:
    """
    Calculate current employee tenure from the real joining date.

    The calculation is calendar-based and does not use hardcoded values.
    """
    if joining_date is None:
        return "Not available"

    today = date.today()

    if joining_date > today:
        return "Not started"

    years = today.year - joining_date.year
    months = today.month - joining_date.month

    if today.day < joining_date.day:
        months -= 1

    if months < 0:
        years -= 1
        months += 12

    if years > 0 and months > 0:
        return f"{years}y {months}m"

    if years > 0:
        return f"{years}y"

    return f"{max(months, 0)}m"


def calculate_profile_completeness(
    employee: Employee,
) -> tuple[int, int, int]:
    """
    Calculate profile completeness from actual employee fields.

    Only fields represented by the employee dashboard are considered.
    """
    fields = [
        employee.employee_id,
        employee.first_name,
        employee.last_name,
        employee.email,
        employee.phone,
        employee.department,
        employee.designation,
        employee.joining_date,
        employee.salary,
        employee.status,
    ]

    total = len(fields)

    completed = sum(
        1
        for field in fields
        if field is not None
        and str(field).strip() != ""
    )

    percentage = (
        int((completed / total) * 100)
        if total
        else 0
    )

    return completed, total, percentage


# ============================================================
# DESIGN SYSTEM
# ============================================================

def render_styles() -> None:
    """Render the employee dashboard design system."""
    from app.ui.theme import get_theme_css
    theme = st.session_state.get("theme", "dark")
    theme_overrides = get_theme_css(theme)
    st.html(f"<style>{theme_overrides}</style>")
    st.html(
        """
        <style>

        /* ====================================================
           ROOT / LAYOUT
           ==================================================== */

        .block-container {
            max-width: 1500px;
            padding-top: 1.25rem;
            padding-bottom: 3.5rem;
        }

        .employee-shell {
            width: 100%;
        }

        .muted {
            color: #64748b;
        }

        /* ====================================================
           HERO
           ==================================================== */

        .command-hero {
            position: relative;
            overflow: hidden;
            margin-bottom: 22px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 22px;
            background:
                linear-gradient(
                    135deg,
                    #0f172a 0%,
                    #172554 52%,
                    #1d4ed8 100%
                );
            color: #ffffff;
            box-shadow:
                0 18px 45px rgba(15, 23, 42, 0.18);
        }

        .command-hero::before {
            content: "";
            position: absolute;
            width: 230px;
            height: 230px;
            right: -70px;
            top: -105px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.07);
        }

        .command-hero::after {
            content: "";
            position: absolute;
            width: 170px;
            height: 170px;
            right: 130px;
            bottom: -115px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.035);
        }

        .hero-layout {
            position: relative;
            z-index: 2;
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .avatar {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 76px;
            height: 76px;
            min-width: 76px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 20px;
            background:
                linear-gradient(
                    135deg,
                    #2563eb,
                    #6366f1
                );
            color: #ffffff;
            font-size: 24px;
            font-weight: 850;
            box-shadow:
                0 12px 30px rgba(0, 0, 0, 0.25);
        }

        .hero-content {
            flex: 1;
            min-width: 0;
        }

        .hero-eyebrow {
            margin-bottom: 5px;
            color: #bfdbfe;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }

        .hero-title {
            margin: 0;
            color: #ffffff;
            font-size: 31px;
            font-weight: 850;
            line-height: 1.2;
            word-break: break-word;
        }

        .hero-subtitle {
            margin-top: 9px;
            color: #cbd5e1;
            font-size: 14px;
            line-height: 1.6;
        }

        .hero-badge {
            position: relative;
            z-index: 3;
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 9px 14px;
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.09);
            color: #f8fafc;
            font-size: 12px;
            font-weight: 800;
            white-space: nowrap;
        }

        /* ====================================================
           SECTION HEADERS
           ==================================================== */

        .section-header {
            margin-top: 28px;
            margin-bottom: 15px;
        }

        .section-kicker {
            margin-bottom: 4px;
            color: #64748b;
            font-size: 10px;
            font-weight: 850;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }

        .section-heading {
            margin: 0;
            color: #0f172a;
            font-size: 22px;
            font-weight: 850;
            line-height: 1.3;
        }

        .section-description {
            margin-top: 5px;
            color: #64748b;
            font-size: 13px;
            line-height: 1.55;
        }

        /* ====================================================
           KPI CARDS
           ==================================================== */

        .kpi-card {
            min-height: 126px;
            padding: 19px;
            border: 1px solid #e2e8f0;
            border-radius: 17px;
            background: #ffffff;
            box-shadow:
                0 7px 22px rgba(15, 23, 42, 0.045);
            transition:
                transform 0.16s ease,
                box-shadow 0.16s ease;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow:
                0 12px 28px rgba(15, 23, 42, 0.075);
        }

        .kpi-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 12px;
        }

        .kpi-label {
            color: #64748b;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .kpi-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 31px;
            height: 31px;
            min-width: 31px;
            border-radius: 9px;
            background: #eff6ff;
            color: #2563eb;
            font-size: 12px;
            font-weight: 850;
        }

        .kpi-value {
            color: #0f172a;
            font-size: 22px;
            font-weight: 850;
            line-height: 1.25;
            overflow-wrap: anywhere;
        }

        .kpi-meta {
            margin-top: 6px;
            color: #94a3b8;
            font-size: 11px;
            line-height: 1.45;
        }

        /* ====================================================
           PANELS
           ==================================================== */

        .panel {
            height: 100%;
            padding: 22px;
            border: 1px solid #e2e8f0;
            border-radius: 19px;
            background: #ffffff;
            box-shadow:
                0 7px 24px rgba(15, 23, 42, 0.04);
        }

        .panel-title {
            margin-bottom: 4px;
            color: #0f172a;
            font-size: 17px;
            font-weight: 850;
        }

        .panel-description {
            margin-bottom: 17px;
            color: #64748b;
            font-size: 12px;
            line-height: 1.5;
        }

        /* ====================================================
           PROFILE IDENTITY
           ==================================================== */

        .profile-identity {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 16px;
        }

        .profile-avatar {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 54px;
            height: 54px;
            min-width: 54px;
            border: 1px solid #dbeafe;
            border-radius: 15px;
            background: #eff6ff;
            color: #1e40af;
            font-size: 17px;
            font-weight: 850;
        }

        .profile-name {
            color: #0f172a;
            font-size: 18px;
            font-weight: 850;
            overflow-wrap: anywhere;
        }

        .profile-role {
            margin-top: 3px;
            color: #64748b;
            font-size: 12px;
            overflow-wrap: anywhere;
        }

        /* ====================================================
           DATA ROW
           ==================================================== */

        .data-row {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            padding: 11px 0;
            border-bottom: 1px solid #f1f5f9;
        }

        .data-row:last-child {
            border-bottom: 0;
        }

        .data-label {
            color: #64748b;
            font-size: 12px;
            line-height: 1.45;
        }

        .data-value {
            max-width: 65%;
            color: #0f172a;
            font-size: 12px;
            font-weight: 750;
            line-height: 1.45;
            text-align: right;
            overflow-wrap: anywhere;
        }

        /* ====================================================
           STATUS
           ==================================================== */

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 850;
            white-space: nowrap;
        }

        .status-pill-active {
            background: #dcfce7;
            color: #166534;
        }

        .status-pill-inactive {
            background: #fee2e2;
            color: #991b1b;
        }

        .status-pill-leave {
            background: #fef3c7;
            color: #92400e;
        }

        .status-pill-neutral {
            background: #e2e8f0;
            color: #334155;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: currentColor;
        }

        /* ====================================================
           COMPLETENESS
           ==================================================== */

        .completion-number {
            color: #0f172a;
            font-size: 34px;
            font-weight: 900;
            line-height: 1.1;
        }

        .completion-label {
            color: #64748b;
            font-size: 12px;
            line-height: 1.5;
        }

        .completion-track {
            width: 100%;
            height: 8px;
            margin-top: 14px;
            overflow: hidden;
            border-radius: 999px;
            background: #e2e8f0;
        }

        .completion-fill {
            height: 100%;
            border-radius: 999px;
            background:
                linear-gradient(
                    90deg,
                    #2563eb,
                    #6366f1
                );
        }

        /* ====================================================
           TIMELINE
           ==================================================== */

        .timeline {
            position: relative;
            padding-left: 27px;
        }

        .timeline::before {
            content: "";
            position: absolute;
            top: 5px;
            bottom: 5px;
            left: 6px;
            width: 2px;
            background: #e2e8f0;
        }

        .timeline-entry {
            position: relative;
            margin-bottom: 22px;
        }

        .timeline-entry:last-child {
            margin-bottom: 0;
        }

        .timeline-dot {
            position: absolute;
            top: 3px;
            left: -27px;
            width: 14px;
            height: 14px;
            border: 3px solid #dbeafe;
            border-radius: 50%;
            background: #2563eb;
        }

        .timeline-date {
            color: #64748b;
            font-size: 11px;
            font-weight: 750;
        }

        .timeline-title {
            margin-top: 3px;
            color: #0f172a;
            font-size: 14px;
            font-weight: 850;
        }

        .timeline-text {
            margin-top: 3px;
            color: #64748b;
            font-size: 12px;
            line-height: 1.55;
        }

        /* ====================================================
           SECURITY
           ==================================================== */

        .security-item {
            margin-bottom: 10px;
            padding: 13px;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            background: #f8fafc;
        }

        .security-item:last-child {
            margin-bottom: 0;
        }

        .security-label {
            color: #64748b;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .security-value {
            margin-top: 4px;
            color: #0f172a;
            font-size: 13px;
            font-weight: 750;
            overflow-wrap: anywhere;
        }

        /* ====================================================
           SERVICES
           ==================================================== */

        .future-card {
            min-height: 142px;
            padding: 19px;
            border: 1px dashed #cbd5e1;
            border-radius: 17px;
            background: #f8fafc;
        }

        .future-icon {
            margin-bottom: 9px;
            color: #64748b;
            font-size: 18px;
        }

        .future-title {
            color: #334155;
            font-size: 14px;
            font-weight: 850;
        }

        .future-status {
            display: inline-block;
            margin-top: 7px;
            padding: 4px 8px;
            border-radius: 999px;
            background: #e2e8f0;
            color: #475569;
            font-size: 9px;
            font-weight: 850;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .future-text {
            margin-top: 7px;
            color: #64748b;
            font-size: 11px;
            line-height: 1.55;
        }

        /* ====================================================
           FOOTER
           ==================================================== */

        .dashboard-footer {
            margin-top: 30px;
            padding-top: 18px;
            border-top: 1px solid #e2e8f0;
            color: #94a3b8;
            font-size: 10px;
            line-height: 1.7;
            text-align: center;
        }

        /* ====================================================
           STREAMLIT BUTTONS
           ==================================================== */

        div.stButton > button {
            border-radius: 10px;
            font-weight: 650;
        }

        /* ====================================================
           ADVANCED ICON SYSTEM
           ==================================================== */

        .ui-icon {
            display: block;
            flex: 0 0 auto;
        }

        .kpi-label-wrap {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            min-width: 0;
        }

        .kpi-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            min-width: 36px;
            border: 1px solid #dbeafe;
            border-radius: 11px;
            background: linear-gradient(145deg, #eff6ff, #f8fbff);
            color: #2563eb;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.9),
                0 4px 12px rgba(37,99,235,.08);
        }

        .kpi-arrow {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            min-width: 28px;
            border: 1px solid #e2e8f0;
            border-radius: 9px;
            background: #f8fafc;
            color: #94a3b8;
        }

        .hero-status-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        .future-card {
            transition:
                transform .18s ease,
                border-color .18s ease,
                box-shadow .18s ease;
        }

        .future-card:hover {
            transform: translateY(-2px);
            border-color: #bfdbfe;
            box-shadow: 0 12px 28px rgba(15,23,42,.06);
        }

        .future-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 42px;
            height: 42px;
            margin-bottom: 12px;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            background: #ffffff;
            color: #64748b;
            box-shadow: 0 4px 12px rgba(15,23,42,.04);
        }

        .future-status {
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        .security-item {
            position: relative;
        }

        .security-item::before {
            content: "";
            position: absolute;
            left: 0;
            top: 10px;
            bottom: 10px;
            width: 3px;
            border-radius: 99px;
            background: #2563eb;
            opacity: .22;
        }

                /* ====================================================
           WORKSPACE TOOLS
           ==================================================== */

        .side-workspace-note {
            margin: 8px 0 16px;
            padding: 12px 13px;
            border: 1px solid rgba(148, 163, 184, .16);
            border-radius: 12px;
            background: rgba(255,255,255,.025);
        }

        .side-workspace-note strong {
            display: block;
            color: #e2e8f0;
            font-size: 11px;
            font-weight: 800;
        }

        .side-workspace-note span {
            display: block;
            margin-top: 4px;
            color: #94a3b8;
            font-size: 10px;
            line-height: 1.5;
        }

        .tool-card {
            min-height: 148px;
            padding: 18px;
            border: 1px solid #e2e8f0;
            border-radius: 17px;
            background: linear-gradient(145deg, #ffffff, #f8fafc);
            box-shadow: 0 7px 22px rgba(15,23,42,.04);
        }

        .tool-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            margin-bottom: 12px;
            border: 1px solid #dbeafe;
            border-radius: 12px;
            background: #eff6ff;
            color: #2563eb;
            font-size: 17px;
            font-weight: 850;
        }

        .tool-title {
            color: #0f172a;
            font-size: 14px;
            font-weight: 850;
        }

        .tool-text {
            margin-top: 6px;
            color: #64748b;
            font-size: 11px;
            line-height: 1.55;
        }

        /* ====================================================
           RESPONSIVE
           ==================================================== */

        @media (max-width: 900px) {

            .command-hero {
                padding: 23px;
            }

            .hero-layout {
                align-items: flex-start;
                flex-wrap: wrap;
            }

            .hero-title {
                font-size: 25px;
            }

            .hero-badge {
                margin-left: 96px;
            }
        }

        @media (max-width: 600px) {

            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .command-hero {
                padding: 19px;
                border-radius: 17px;
            }

            .hero-layout {
                gap: 13px;
            }

            .avatar {
                width: 60px;
                height: 60px;
                min-width: 60px;
                border-radius: 16px;
                font-size: 19px;
            }

            .hero-title {
                font-size: 21px;
            }

            .hero-subtitle {
                font-size: 12px;
            }

            .hero-badge {
                margin-left: 0;
            }

            .section-heading {
                font-size: 19px;
            }

            .panel {
                padding: 17px;
                border-radius: 16px;
            }

            .data-row {
                gap: 10px;
            }

            .data-value {
                max-width: 58%;
            }
        }

        /* FINAL THEME / READABILITY / ICON OVERRIDES */

        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background: #f4f7fb;
        }

        [data-testid="stHeader"] {
            background: rgba(244, 247, 251, 0.96);
        }

        .main .block-container { color: #0f172a; }

        .section-kicker { color: #2563eb; }

        .section-heading,
        .kpi-value,
        .panel-title,
        .profile-name,
        .data-value,
        .timeline-title,
        .security-value,
        .completion-number {
            color: #0f172a;
        }

        .section-description,
        .panel-description,
        .data-label,
        .timeline-text,
        .kpi-meta {
            color: #64748b;
        }

        .kpi-card, .panel {
            background: #ffffff;
            color: #0f172a;
        }

        .dashboard-glyph {
            position: relative;
            display: inline-flex;
            width: 18px;
            height: 18px;
            align-items: center;
            justify-content: center;
            color: currentColor;
        }

        .dashboard-glyph::before,
        .dashboard-glyph::after {
            content: "";
            position: absolute;
            box-sizing: border-box;
        }

        .glyph-id::before {
            width: 15px; height: 11px;
            border: 1.8px solid currentColor;
            border-radius: 3px;
        }

        .glyph-id::after {
            width: 6px; height: 1.8px;
            background: currentColor;
            left: 8px; top: 7px;
            box-shadow: 0 -4px 0 currentColor;
        }

        .glyph-tenure::before {
            width: 15px; height: 15px;
            border: 1.8px solid currentColor;
            border-radius: 50%;
        }

        .glyph-tenure::after {
            width: 1.8px; height: 5px;
            background: currentColor;
            left: 8px; top: 4px;
        }

        .glyph-department::before {
            width: 13px; height: 14px;
            border: 1.8px solid currentColor;
            border-radius: 2px;
        }

        .glyph-department::after {
            width: 2px; height: 2px;
            background: currentColor;
            left: 6px; top: 6px;
            box-shadow: 5px 0 currentColor, 0 5px currentColor, 5px 5px currentColor;
        }

        .glyph-designation::before {
            width: 14px; height: 11px;
            border: 1.8px solid currentColor;
            border-radius: 3px;
            top: 6px;
        }

        .glyph-designation::after {
            width: 6px; height: 4px;
            border: 1.8px solid currentColor;
            border-bottom: 0;
            border-radius: 3px 3px 0 0;
            top: 2px;
        }

        .glyph-info::before {
            width: 15px; height: 15px;
            border: 1.8px solid currentColor;
            border-radius: 50%;
        }

        .glyph-info::after {
            content: "i";
            position: absolute;
            top: 1px; left: 7px;
            font-size: 11px; font-weight: 900;
        }

        .kpi-icon { color: #2563eb; }
        .kpi-arrow { color: #64748b; }

        .glyph-attendance::before,
        .glyph-leave::before {
            width: 14px;
            height: 14px;
            border: 1.8px solid currentColor;
            border-radius: 3px;
        }

        .glyph-attendance::after {
            width: 6px;
            height: 3px;
            border-left: 1.8px solid currentColor;
            border-bottom: 1.8px solid currentColor;
            transform: rotate(-45deg);
            top: 5px;
        }

        .glyph-leave::after {
            width: 7px;
            height: 7px;
            border: 1.8px solid currentColor;
            border-radius: 50%;
            top: 3px;
        }

        .glyph-request::before {
            width: 13px;
            height: 15px;
            border: 1.8px solid currentColor;
            border-radius: 2px;
        }

        .glyph-request::after {
            width: 6px;
            height: 1.8px;
            background: currentColor;
            top: 7px;
            box-shadow: 0 4px 0 currentColor;
        }

        .glyph-shield::before {
            width: 14px;
            height: 16px;
            border: 1.8px solid currentColor;
            border-radius: 7px 7px 8px 8px;
            transform: scaleX(.82) rotate(45deg);
        }

        .glyph-lock::before {
            width: 12px;
            height: 9px;
            border: 1.8px solid currentColor;
            border-radius: 2px;
            top: 7px;
        }

        .glyph-lock::after {
            width: 7px;
            height: 7px;
            border: 1.8px solid currentColor;
            border-bottom: 0;
            border-radius: 6px 6px 0 0;
            top: 2px;
        }

        section[data-testid="stSidebar"] {
            background: #111827;
            border-right: 1px solid #1f2937;
        }

        section[data-testid="stSidebar"] > div { background: #111827; }

        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4 {
            color: #e5e7eb;
        }

        section[data-testid="stSidebar"] hr { border-color: #334155; }

        section[data-testid="stSidebar"] .stButton > button {
            border: 1px solid #334155;
            background: #1f2937;
            color: #e5e7eb;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            border-color: #60a5fa;
            background: #263449;
            color: #ffffff;
        }



        /* ====================================================
           STRUCTURED EMPLOYEE PORTAL — FINAL VISUAL SYSTEM
           ==================================================== */

        :root {
            color-scheme: light;
        }

        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background: #f6f8fc !important;
        }

        [data-testid="stHeader"] {
            background: rgba(246, 248, 252, 0.92) !important;
            border-bottom: 1px solid #e5eaf2;
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1440px !important;
            padding-top: 28px !important;
            padding-left: 34px !important;
            padding-right: 34px !important;
            padding-bottom: 64px !important;
        }

        .section-header {
            margin-top: 38px;
            margin-bottom: 18px;
            padding-left: 2px;
        }

        .section-kicker {
            color: #3563e9 !important;
            font-size: 10px !important;
            letter-spacing: .16em !important;
        }

        .section-heading {
            color: #101828 !important;
            font-size: 24px !important;
            letter-spacing: -.025em;
        }

        .section-description {
            color: #667085 !important;
            max-width: 780px;
        }

        .command-hero {
            margin-bottom: 34px;
            padding: 30px 34px;
            min-height: 148px;
            border: 1px solid #dce5ff;
            border-radius: 24px;
            background:
                radial-gradient(circle at 88% 20%, rgba(255,255,255,.17) 0 11%, transparent 12%),
                radial-gradient(circle at 76% 120%, rgba(255,255,255,.10) 0 14%, transparent 15%),
                linear-gradient(120deg, #101c3d 0%, #1d3f9f 52%, #2f5eea 100%) !important;
            box-shadow: 0 20px 48px rgba(31, 63, 145, .16);
        }

        .avatar {
            width: 76px;
            height: 76px;
            border-radius: 22px;
            background: linear-gradient(145deg, #ffffff, #dbe7ff);
            color: #2348bb;
            border: 1px solid rgba(255,255,255,.7);
            box-shadow: 0 12px 26px rgba(0,0,0,.18);
        }

        .hero-eyebrow {
            color: #bcd0ff !important;
            font-size: 10px;
            letter-spacing: .17em;
        }

        .hero-title {
            font-size: 32px;
            letter-spacing: -.035em;
        }

        .hero-subtitle {
            color: #dbe6ff !important;
            font-size: 14px;
        }

        .hero-badge {
            padding: 10px 15px;
            background: rgba(255,255,255,.10);
            border-color: rgba(255,255,255,.24);
            backdrop-filter: blur(8px);
        }

        .kpi-card {
            min-height: 144px;
            padding: 21px;
            border: 1px solid #e2e8f2;
            border-radius: 18px;
            background: #ffffff !important;
            box-shadow: 0 8px 24px rgba(16,24,40,.045);
        }

        .kpi-card:hover {
            border-color: #cbd8f5;
            box-shadow: 0 14px 30px rgba(16,24,40,.08);
            transform: translateY(-3px);
        }

        .kpi-icon {
            width: 40px;
            height: 40px;
            border-radius: 12px;
            background: #eef4ff;
            border: 1px solid #d8e5ff;
            color: #3563e9;
        }

        .kpi-arrow {
            width: 30px;
            height: 30px;
            border-radius: 10px;
            color: #98a2b3;
            background: #f8fafc;
        }

        .kpi-label {
            color: #667085 !important;
            font-size: 10px;
            letter-spacing: .09em;
        }

        .kpi-value {
            color: #101828 !important;
            font-size: 25px;
            letter-spacing: -.02em;
        }

        .kpi-meta {
            color: #98a2b3 !important;
        }

        .panel {
            padding: 24px;
            border: 1px solid #e2e8f2;
            border-radius: 20px;
            background: #ffffff !important;
            box-shadow: 0 8px 24px rgba(16,24,40,.04);
        }

        .panel-title,
        .profile-name,
        .data-value,
        .timeline-title,
        .security-value,
        .completion-number {
            color: #101828 !important;
        }

        .panel-description,
        .data-label,
        .timeline-text {
            color: #667085 !important;
        }

        .data-row {
            padding: 13px 0;
            border-bottom-color: #eef2f6;
        }

        .data-label {
            font-size: 11px;
            font-weight: 650;
        }

        .data-value {
            font-weight: 750;
        }

        .future-card {
            min-height: 190px;
            padding: 22px;
            border: 1px solid #e2e8f2;
            border-radius: 18px;
            background: #ffffff !important;
            box-shadow: 0 7px 22px rgba(16,24,40,.035);
        }

        .future-icon {
            width: 46px;
            height: 46px;
            border-radius: 13px;
            background: #f4f7fb;
            border-color: #e1e7ef;
            color: #667085;
        }

        /* SIDEBAR */
        section[data-testid="stSidebar"] {
            background: #101828 !important;
            border-right: 1px solid #1d2939 !important;
        }

        section[data-testid="stSidebar"] > div,
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            background: #101828 !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding: 24px 18px 26px !important;
        }

        .side-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 0;
            padding: 4px 2px 18px;
            border-bottom: 1px solid #243147;
        }

        .side-brand > div:last-child {
            min-width: 0;
        }

        .side-brand-title {
            white-space: nowrap;
            font-size: 15px;
        }

        .side-brand-subtitle {
            white-space: nowrap;
            font-size: 7px;
            letter-spacing: .10em;
        }

        .side-brand-mark {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 12px;
            background: linear-gradient(145deg, #3563e9, #5d75f3);
            color: white;
            box-shadow: 0 8px 18px rgba(53,99,233,.25);
        }

        .side-brand-title {
            color: #f8fafc;
            font-size: 16px;
            font-weight: 800;
        }

        .side-brand-subtitle {
            margin-top: 3px;
            color: #8492a8;
            font-size: 8px;
            font-weight: 750;
            letter-spacing: .12em;
        }

        .side-profile {
            position: relative;
            display: flex;
            align-items: center;
            gap: 11px;
            margin: 20px 0 24px;
            padding: 14px;
            border: 1px solid #26344a;
            border-radius: 15px;
            background: #172236;
        }

        .side-profile-avatar {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: #e9efff;
            color: #2348bb;
            font-size: 13px;
            font-weight: 850;
        }

        .side-profile-copy {
            min-width: 0;
            padding-right: 10px;
        }

        .side-profile-name {
            color: #f8fafc;
            font-size: 12px;
            font-weight: 750;
            overflow-wrap: anywhere;
        }

        .side-profile-id {
            margin-top: 3px;
            color: #8492a8;
            font-size: 10px;
        }

        .side-status-dot {
            position: absolute;
            right: 12px;
            top: 13px;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #32d583;
            box-shadow: 0 0 0 4px rgba(50,213,131,.10);
        }

        .side-section-label {
            margin: 0 4px 9px;
            color: #66768e;
            font-size: 9px;
            font-weight: 800;
            letter-spacing: .16em;
        }

        .side-fact {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 9px 4px;
            border-bottom: 1px solid #1d2939;
        }

        .side-fact span {
            color: #8492a8;
            font-size: 10px;
        }

        .side-fact strong {
            color: #dbe3ef;
            font-size: 10px;
            font-weight: 700;
            text-align: right;
            overflow-wrap: anywhere;
        }

        .side-services-label {
            margin-top: 24px;
        }

        section[data-testid="stSidebar"] .stButton {
            margin: 5px 0;
        }

        section[data-testid="stSidebar"] .stButton > button {
            min-height: 42px;
            justify-content: flex-start;
            border: 1px solid #243147 !important;
            border-radius: 11px !important;
            background: #172236 !important;
            color: #cbd5e1 !important;
            font-size: 11px;
            font-weight: 650;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            border-color: #38527a !important;
            background: #1c2b43 !important;
            color: #ffffff !important;
        }

        section[data-testid="stSidebar"] .stButton > button:disabled {
            opacity: .68;
        }

        .side-account {
            margin-top: 22px;
            padding: 14px;
            border: 1px solid #243147;
            border-radius: 13px;
            background: #0d1524;
        }

        .side-account-label {
            color: #66768e;
            font-size: 8px;
            font-weight: 800;
            letter-spacing: .14em;
        }

        .side-account-value {
            margin-top: 5px;
            color: #e7edf7;
            font-size: 11px;
            font-weight: 750;
            overflow-wrap: anywhere;
        }

        .side-account-role {
            margin-top: 3px;
            color: #8492a8;
            font-size: 9px;
        }

        section[data-testid="stSidebar"] hr {
            display: none;
        }

        /* STREAMLIT NATIVE TEXT SAFETY */
        [data-testid="stMain"] p,
        [data-testid="stMain"] label {
            color: #344054;
        }

        @media (max-width: 900px) {
            [data-testid="stMainBlockContainer"] {
                padding-left: 18px !important;
                padding-right: 18px !important;
            }
            .command-hero {
                padding: 24px;
            }
        }

        @media (max-width: 600px) {
            [data-testid="stMainBlockContainer"] {
                padding-left: 12px !important;
                padding-right: 12px !important;
            }
            .hero-title {
                font-size: 24px;
            }
        }

        

        /* ====================================================
           PREMIUM COMMAND-CENTER LAYOUT
           ==================================================== */
        .premium-command-center {
            margin: 10px 0 30px;
            padding: 30px;
            border: 1px solid #dbe4f0;
            border-radius: 24px;
            background: linear-gradient(135deg, #ffffff 0%, #f8fbff 62%, #eef5ff 100%);
            box-shadow: 0 18px 45px rgba(15, 23, 42, .08);
        }
        .command-topline { display:flex; align-items:center; justify-content:space-between; gap:28px; }
        .command-kicker,.advanced-kicker { color:#2563eb; font-size:11px; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }
        .command-heading { margin-top:7px; color:#0f172a; font-size:28px; line-height:1.15; font-weight:800; letter-spacing:-.035em; }
        .command-subtitle { margin-top:8px; color:#64748b; font-size:13px; max-width:680px; }
        .command-context { display:flex; align-items:center; gap:10px; min-width:180px; padding:12px 15px; border:1px solid #dbe7f7; border-radius:14px; background:#fff; color:#0f172a; }
        .command-context strong { display:block; font-size:12px; }
        .command-context small { display:block; margin-top:2px; color:#64748b; font-size:11px; }
        .command-context-icon { display:grid; place-items:center; width:34px; height:34px; border-radius:10px; background:#eff6ff; color:#2563eb; }
        .command-metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-top:25px; }
        .command-metric { display:flex; align-items:center; gap:12px; padding:15px; border:1px solid #e1e8f2; border-radius:15px; background:rgba(255,255,255,.82); }
        .metric-icon,.panel-icon,.insight-icon { display:grid; place-items:center; flex:0 0 auto; width:40px; height:40px; border-radius:12px; color:#2563eb; background:#eff6ff; border:1px solid #dbeafe; }
        .command-metric small,.insight-card small,.security-grid small,.advanced-data-grid small,.position-highlight small { display:block; color:#64748b; font-size:9px; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
        .command-metric strong { display:block; margin-top:3px; color:#0f172a; font-size:15px; }
        .advanced-grid { display:grid; gap:18px; margin:0 0 18px; }
        .two-up { grid-template-columns:1fr 1fr; }
        .three-up { grid-template-columns:repeat(3,1fr); }
        .advanced-panel,.insight-card { border:1px solid #dbe4ef; border-radius:20px; background:#fff; box-shadow:0 12px 32px rgba(15,23,42,.055); }
        .advanced-panel { padding:23px; }
        .advanced-panel-head { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; }
        .advanced-panel-head h3 { margin:5px 0 3px; color:#0f172a; font-size:19px; letter-spacing:-.02em; }
        .advanced-panel-head p { margin:0; color:#64748b; font-size:12px; line-height:1.5; }
        .identity-banner { display:flex; align-items:center; gap:12px; margin:22px 0 17px; padding:13px; border-radius:14px; background:#f8fafc; border:1px solid #e8edf4; }
        .identity-avatar { display:grid; place-items:center; width:43px; height:43px; border-radius:12px; background:linear-gradient(135deg,#2563eb,#4f46e5); color:#fff; font-weight:800; }
        .identity-banner strong { display:block; color:#0f172a; font-size:14px; }
        .identity-banner span { display:block; margin-top:3px; color:#64748b; font-size:11px; }
        .advanced-data-grid { display:grid; grid-template-columns:1fr 1fr; gap:0 22px; }
        .advanced-data-grid > div { padding:12px 0; border-top:1px solid #edf1f6; }
        .advanced-data-grid strong { display:block; margin-top:4px; color:#172033; font-size:13px; overflow-wrap:anywhere; }
        .position-highlight { display:flex; align-items:center; justify-content:space-between; gap:14px; margin:22px 0 8px; padding:15px; border-radius:15px; background:linear-gradient(135deg,#eff6ff,#f8fafc); border:1px solid #dbeafe; }
        .position-highlight strong { display:block; margin-top:4px; color:#0f172a; font-size:17px; }
        .status-chip { display:inline-flex; align-items:center; gap:7px; padding:7px 10px; border-radius:999px; background:#dcfce7; color:#166534; font-size:11px; font-weight:800; }
        .status-chip span { width:7px; height:7px; border-radius:50%; background:#16a34a; }
        .insight-card { display:flex; gap:14px; padding:19px; }
        .insight-card strong { display:block; margin-top:4px; color:#0f172a; font-size:17px; }
        .insight-card p { margin:5px 0 0; color:#64748b; font-size:11px; line-height:1.45; }
        .quality-panel,.security-panel { min-height:190px; }
        .quality-score { display:flex; align-items:baseline; gap:9px; margin-top:22px; }
        .quality-score strong { color:#0f172a; font-size:34px; letter-spacing:-.04em; }
        .quality-score span { color:#64748b; font-size:11px; }
        .quality-track { height:9px; margin-top:13px; overflow:hidden; border-radius:99px; background:#e8eef7; }
        .quality-track span { display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,#2563eb,#4f46e5); }
        .quality-foot { display:flex; justify-content:space-between; margin-top:11px; color:#64748b; font-size:11px; }
        .security-grid { display:grid; grid-template-columns:1fr 1fr; gap:0 22px; margin-top:20px; }
        .security-grid > div { padding:12px 0; border-top:1px solid #edf1f6; }
        .security-grid strong { display:block; margin-top:4px; color:#172033; font-size:12px; overflow-wrap:anywhere; }
        @media (max-width: 1000px) {
            .command-metrics { grid-template-columns:1fr 1fr; }
            .two-up,.three-up { grid-template-columns:1fr; }
            .command-topline { align-items:flex-start; flex-direction:column; }
            .command-context { width:100%; box-sizing:border-box; }
        }
        @media (max-width: 650px) {
            .premium-command-center { padding:20px; border-radius:18px; }
            .command-heading { font-size:22px; }
            .command-metrics { grid-template-columns:1fr; }
            .advanced-data-grid,.security-grid { grid-template-columns:1fr; }
        }


        /* ====================================================
           INTERNAL COLLAPSIBLE EMPLOYEE PANEL
           ==================================================== */

        .internal-employee-panel {
            position: sticky;
            top: 18px;
            padding: 19px;
            border: 1px solid #dbe4ef;
            border-radius: 20px;
            background: linear-gradient(180deg, #0f172a 0%, #172554 100%);
            color: #ffffff;
            box-shadow: 0 14px 35px rgba(15, 23, 42, .13);
        }

        .internal-panel-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
        }

        .internal-panel-kicker {
            color: #93c5fd;
            font-size: 9px;
            font-weight: 850;
            letter-spacing: .13em;
        }

        .internal-panel-head h3 {
            margin: 5px 0 0;
            color: #ffffff;
            font-size: 18px;
            font-weight: 850;
        }

        .internal-panel-head p {
            margin: 5px 0 0;
            color: #94a3b8;
            font-size: 10px;
            line-height: 1.45;
        }

        .internal-panel-avatar {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 42px;
            height: 42px;
            min-width: 42px;
            border: 1px solid rgba(255,255,255,.16);
            border-radius: 12px;
            background: linear-gradient(135deg, #2563eb, #6366f1);
            color: #ffffff;
            font-size: 13px;
            font-weight: 900;
        }

        .internal-identity {
            margin: 18px 0 12px;
            padding: 13px;
            border: 1px solid rgba(148,163,184,.14);
            border-radius: 13px;
            background: rgba(255,255,255,.045);
        }

        .internal-identity strong,
        .internal-identity span {
            display: block;
            overflow-wrap: anywhere;
        }

        .internal-identity strong {
            color: #f8fafc;
            font-size: 14px;
        }

        .internal-identity span {
            margin-top: 4px;
            color: #94a3b8;
            font-size: 10px;
        }

        .internal-data-row {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 10px;
            padding: 11px 2px;
            border-bottom: 1px solid rgba(148,163,184,.12);
        }

        .internal-data-row span {
            color: #94a3b8;
            font-size: 10px;
        }

        .internal-data-row strong {
            max-width: 58%;
            color: #e2e8f0;
            font-size: 10px;
            text-align: right;
            overflow-wrap: anywhere;
        }

        .internal-panel-note {
            display: flex;
            align-items: center;
            gap: 9px;
            margin-top: 15px;
            padding: 10px;
            border: 1px solid rgba(96,165,250,.18);
            border-radius: 12px;
            background: rgba(37,99,235,.10);
        }

        .internal-panel-note-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 25px;
            height: 25px;
            min-width: 25px;
            border-radius: 8px;
            background: rgba(34,197,94,.15);
            color: #86efac;
            font-size: 12px;
            font-weight: 900;
        }

        .internal-panel-note strong,
        .internal-panel-note span {
            display: block;
        }

        .internal-panel-note strong {
            color: #e2e8f0;
            font-size: 10px;
        }

        .internal-panel-note div span {
            margin-top: 2px;
            color: #94a3b8;
            font-size: 9px;
        }

        .internal-employee-panel + div.stButton {
            margin-top: 8px;
        }

        @media (max-width: 900px) {
            .internal-employee-panel {
                position: static;
            }
        }
</style>
        """,
    )


# ============================================================
# ADVANCED NAVIGATION / WORKSPACE CONTROLS
# ============================================================

def render_navigation_styles() -> None:
    """Add compact navigation and sidebar interaction styling."""
    st.html(
        """
        <style>
        [data-testid="stSidebar"] {
            border-right: 1px solid #dbe4f0;
        }

        [data-testid="stSidebar"] .stButton > button {
            min-height: 40px;
            border-radius: 10px;
        }

        /* Compact, readable employee sidebar navigation */
        section[data-testid="stSidebar"] .block-container {
            padding: 18px 14px 22px !important;
        }

        section[data-testid="stSidebar"] [data-testid="stRadio"] > label {
            display: none;
        }

        section[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {
            gap: 4px;
        }

        section[data-testid="stSidebar"] [data-testid="stRadio"] label {
            display: flex;
            align-items: center;
            gap: 9px;
            width: 100%;
            min-width: 0;
            margin: 0;
            padding: 5px 2px;
        }

        section[data-testid="stSidebar"] [data-testid="stRadio"] label p {
            margin: 0;
            font-size: 13px !important;
            line-height: 1.35 !important;
            white-space: nowrap;
            overflow-wrap: normal;
            word-break: keep-all;
        }

        section[data-testid="stSidebar"] [data-testid="stExpander"] {
            margin-bottom: 10px;
            border-radius: 12px;
            overflow: hidden;
        }

        section[data-testid="stSidebar"] [data-testid="stExpander"] summary {
            min-height: 44px;
        }

        .workspace-toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            margin: 0 0 18px;
            padding: 12px 15px;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            background: rgba(255,255,255,.88);
            box-shadow: 0 5px 18px rgba(15,23,42,.035);
        }

        .toolbar-label {
            color: #64748b;
            font-size: 10px;
            font-weight: 850;
            letter-spacing: .12em;
            text-transform: uppercase;
        }

        .toolbar-value {
            margin-top: 2px;
            color: #0f172a;
            font-size: 13px;
            font-weight: 800;
        }

        .integrity-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0,1fr));
            gap: 10px;
            margin-top: 14px;
        }

        .integrity-item {
            padding: 12px;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            background: #f8fafc;
        }

        .integrity-item small {
            display: block;
            color: #64748b;
            font-size: 9px;
            font-weight: 800;
            letter-spacing: .06em;
            text-transform: uppercase;
        }

        .integrity-item strong {
            display: block;
            margin-top: 5px;
            color: #0f172a;
            font-size: 12px;
        }

        .integrity-ok { color: #15803d !important; }
        .integrity-warn { color: #b45309 !important; }

        @media (max-width: 900px) {
            .integrity-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
        }

        @media (max-width: 600px) {
            .integrity-grid { grid-template-columns: 1fr; }
        }
        </style>
        """,
    )


def get_employee_view() -> str:
    """Return the selected employee workspace view."""
    return st.session_state.get("employee_view", "All sections")


def render_workspace_toolbar(employee: Employee, user: User) -> None:
    """Render a compact, real-data workspace toolbar."""
    view = get_employee_view()
    st.html(
        f"""
        <div class="workspace-toolbar">
            <div>
                <div class="toolbar-label">Current workspace</div>
                <div class="toolbar-value">{safe_text(view)}</div>
            </div>
            <div>
                <div class="toolbar-label">Authenticated as</div>
                <div class="toolbar-value">{safe_text(user.username, full_name(employee))}</div>
            </div>
        </div>
        """,
    )


def render_data_integrity(employee: Employee, user: User) -> None:
    """Render real integrity checks without inventing data."""
    checks = [
        ("Employee mapping", user.employee_id == employee.id),
        ("Account active", bool(user.is_active)),
        ("Employee ID", bool(raw_text(employee.employee_id))),
        ("Core profile", bool(employee.first_name and employee.last_name and employee.email)),
        ("Employment data", bool(employee.department and employee.designation and employee.joining_date)),
        ("Contact data", bool(employee.email and employee.phone)),
    ]
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    status = "Healthy" if passed == total else "Needs review"
    css = "integrity-ok" if passed == total else "integrity-warn"

    section_header(
        "SYSTEM HEALTH",
        "Workspace integrity",
        "Validation checks are calculated from the authenticated account and its linked employee record.",
    )

    st.html(
        f"""
        <div class="panel">
            <div class="panel-title">{status}</div>
            <div class="panel-description">{passed} of {total} integrity checks passed.</div>
            <div class="integrity-grid">
                {''.join(
                    f'<div class="integrity-item"><small>{escape(label)}</small><strong class="{css if ok else "integrity-warn"}">{"✓ Verified" if ok else "! Review"}</strong></div>'
                    for label, ok in checks
                )}
            </div>
        </div>
        """,
    )


def render_missing_profile_fields(employee: Employee) -> None:
    """Show real missing profile fields when present."""
    fields = {
        "Employee ID": employee.employee_id,
        "First name": employee.first_name,
        "Last name": employee.last_name,
        "Email": employee.email,
        "Phone": employee.phone,
        "Department": employee.department,
        "Designation": employee.designation,
        "Joining date": employee.joining_date,
        "Salary": employee.salary,
        "Status": employee.status,
    }
    missing = [label for label, value in fields.items() if value is None or str(value).strip() == ""]

    with st.expander("Profile data audit", expanded=False):
        if missing:
            st.warning("The following fields are incomplete: " + ", ".join(missing))
        else:
            st.success("All dashboard profile fields are populated.")


# ============================================================
# UI COMPONENTS
# ============================================================

def section_header(
    kicker: str,
    title: str,
    description: str,
) -> None:
    """Render a reusable section heading."""
    st.html(
        f"""
        <div class="section-header">
            <div class="section-kicker">
                {escape(kicker)}
            </div>

            <div class="section-heading">
                {escape(title)}
            </div>

            <div class="section-description">
                {escape(description)}
            </div>
        </div>
        """,
    )


def data_row(
    label: str,
    value: str,
) -> None:
    """Render a reusable information row."""
    st.html(
        f"""
        <div class="data-row">
            <div class="data-label">
                {escape(label)}
            </div>

            <div class="data-value">
                {escape(value)}
            </div>
        </div>
        """,
    )


def render_kpi_card(
    label: str,
    value: str,
    meta: str,
    icon: str,
) -> None:
    """Render a premium KPI card with a consistent vector icon."""
    st.html(
        f"""
        <article class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label-wrap">
                    <div class="kpi-icon">
                        <span class="dashboard-glyph glyph-{escape(icon)}" aria-hidden="true"></span>
                    </div>
                    <div class="kpi-label">{escape(label)}</div>
                </div>
                <div class="kpi-arrow">
                    <span class="dashboard-glyph glyph-info" aria-hidden="true"></span>
                </div>
            </div>

            <div class="kpi-value">{escape(value)}</div>
            <div class="kpi-meta">{escape(meta)}</div>
        </article>
        """,
    )


def render_status_pill(status: object) -> None:
    """Render a semantic employment status indicator."""
    display_status = format_status(status)
    css_status = status_class(status)

    st.html(
        f"""
        <span class="status-pill status-pill-{css_status}">
            <span class="status-dot"></span>
            {escape(display_status)}
        </span>
        """,
    )


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar(
    employee: Employee,
    user: User,
) -> None:
    """Render compact employee navigation with collapsible control groups."""
    with st.sidebar:
        st.html(
            f"""
            <div class="side-brand">
                <div class="side-brand-mark"><span class="dashboard-glyph glyph-profile" aria-hidden="true"></span></div>
                <div>
                    <div class="side-brand-title">Employee Portal</div>
                    <div class="side-brand-subtitle">SELF-SERVICE COMMAND CENTER</div>
                </div>
            </div>

            <div class="side-profile">
                <div class="side-profile-avatar">{escape(initials(employee))}</div>
                <div class="side-profile-copy">
                    <div class="side-profile-name">{escape(full_name(employee))}</div>
                    <div class="side-profile-id">{escape(raw_text(employee.employee_id, "ID unavailable"))}</div>
                </div>
                <span class="side-status-dot"></span>
            </div>

            """,
        )

        current_theme = st.session_state.get("theme", "dark")
        is_dark = (current_theme == "dark")
        emp_theme_toggle = st.toggle(
            "🌙 Dark Mode" if is_dark else "☀️ Light Mode",
            value=is_dark,
            key="emp_theme_toggle",
        )
        new_theme = "dark" if emp_theme_toggle else "light"
        if new_theme != current_theme:
            st.session_state["theme"] = new_theme
            st.rerun()

        with st.expander("Workspace navigation", expanded=True):
            view_options = [
                "All sections",
                "Overview",
                "Leave Center",
                "Daily Attendance",
                "My Payslip",
                "Notice Board",
                "Profile & employment",
                "Security",
                "Data center",
            ]
            current = get_employee_view()
            if current not in view_options:
                current = "All sections"
            selected = st.radio(
                "Workspace section",
                view_options,
                index=view_options.index(current),
                key="employee_view_selector",
                label_visibility="collapsed",
            )
            st.session_state["employee_view"] = selected

        with st.expander("Employment summary", expanded=True):
            st.html(
                f"""
                <div class="side-fact"><span>Department</span><strong>{escape(raw_text(employee.department, "Not available"))}</strong></div>
                <div class="side-fact"><span>Designation</span><strong>{escape(raw_text(employee.designation, "Not available"))}</strong></div>
                <div class="side-fact"><span>Status</span><strong>{escape(format_status(employee.status))}</strong></div>
                """,
            )

        with st.expander("Workspace controls", expanded=True):
            if st.button("Refresh workspace", icon=":material/refresh:", width="stretch", key="employee_refresh"):
                st.rerun()
            if st.button("Open all sections", icon=":material/dashboard:", width="stretch", key="employee_open_all"):
                st.session_state["employee_view"] = "All sections"
                st.rerun()

        with st.expander("Privacy & display", expanded=False):
            hide_salary = st.checkbox(
                "Hide salary on screen",
                value=st.session_state.get("employee_hide_salary", False),
                key="employee_hide_salary_sidebar",
            )
            st.session_state["employee_hide_salary"] = hide_salary
            st.caption("Display-only control. Your database record is not changed.")

        with st.expander("Account", expanded=False):
            st.html(
                f"""
                <div class="side-account">
                    <div class="side-account-label">SIGNED IN ACCOUNT</div>
                    <div class="side-account-value">{escape(raw_text(user.username, "Employee"))}</div>
                    <div class="side-account-role">Employee access</div>
                </div>
                """,
            )
            if st.button("Logout", type="secondary", icon=":material/logout:", width="stretch", key="employee_logout"):
                logout()


# ============================================================
# HERO
# ============================================================

def render_hero(employee: Employee) -> None:
    """Render employee identity hero section."""
    employee_name = safe_text(full_name(employee))
    employee_id = safe_text(employee.employee_id)
    department = safe_text(employee.department)
    designation = safe_text(employee.designation)
    employee_initials = safe_text(initials(employee))
    status = format_status(employee.status)

    st.html(
        f"""
        <div class="command-hero">

            <div class="hero-layout">

                <div class="avatar">
                    {employee_initials}
                </div>

                <div class="hero-content">

                    <div class="hero-eyebrow">
                        Employee Self-Service
                    </div>

                    <div class="hero-title">
                        Welcome, {employee_name}
                    </div>

                    <div class="hero-subtitle">
                        {designation}
                        &nbsp;•&nbsp;
                        {department}
                        &nbsp;•&nbsp;
                        Employee ID: {employee_id}
                    </div>

                </div>

                <div class="hero-badge">
                    <span class="hero-status-icon">
                        <span class="dashboard-glyph glyph-shield" aria-hidden="true"></span>
                    </span>
                    {escape(status)}
                </div>

            </div>

        </div>
        """,
    )


# ============================================================
# EMPLOYMENT SNAPSHOT
# ============================================================

def render_overview(employee: Employee) -> None:
    """Render meaningful employee-level KPIs."""
    section_header(
        "PERSONAL SNAPSHOT",
        "Your employment at a glance",
        "Key information calculated directly from your authenticated employee profile.",
    )

    tenure = calculate_tenure(employee.joining_date)

    columns = st.columns(
        4,
        gap="medium",
    )

    with columns[0]:
        render_kpi_card(
            "Employee ID",
            raw_text(
                employee.employee_id,
                "Not available",
            ),
            "Unique employee identifier",
            "id",
        )

    with columns[1]:
        render_kpi_card(
            "Tenure",
            tenure,
            (
                f"Since {format_date(employee.joining_date)}"
                if employee.joining_date
                else "Joining date unavailable"
            ),
            "tenure",
        )

    with columns[2]:
        render_kpi_card(
            "Department",
            raw_text(
                employee.department,
                "Not available",
            ),
            "Current organizational unit",
            "department",
        )

    with columns[3]:
        render_kpi_card(
            "Designation",
            raw_text(
                employee.designation,
                "Not available",
            ),
            "Current job position",
            "designation",
        )


# ============================================================
# PROFILE + EMPLOYMENT
# ============================================================

def render_profile_and_employment(
    employee: Employee,
) -> None:
    """Render personal and employment information."""
    section_header(
        "EMPLOYEE PROFILE",
        "Personal & employment information",
        "Information is loaded only from the employee profile linked to your authenticated account.",
    )

    left, right = st.columns(
        [1, 1],
        gap="large",
    )

    with left:

        st.html(
            """
            <div class="panel">

                <div class="panel-title">
                    Personal Identity
                </div>

                <div class="panel-description">
                    Core contact information
                </div>
            """,
        )

        st.html(
            f"""
            <div class="profile-identity">

                <div class="profile-avatar">
                    {safe_text(initials(employee))}
                </div>

                <div>
                    <div class="profile-name">
                        {safe_text(full_name(employee))}
                    </div>

                    <div class="profile-role">
                        {safe_text(employee.email)}
                    </div>
                </div>

            </div>
            """,
        )

        data_row(
            "First Name",
            safe_text(employee.first_name),
        )

        data_row(
            "Last Name",
            safe_text(employee.last_name),
        )

        data_row(
            "Email",
            safe_text(employee.email),
        )

        data_row(
            "Phone",
            safe_text(employee.phone),
        )

        st.html(
            "</div>",
        )

    with right:

        st.html(
            """
            <div class="panel">

                <div class="panel-title">
                    Employment Identity
                </div>

                <div class="panel-description">
                    Current organizational information
                </div>
            """,
        )

        data_row(
            "Employee ID",
            safe_text(employee.employee_id),
        )

        data_row(
            "Department",
            safe_text(employee.department),
        )

        data_row(
            "Designation",
            safe_text(employee.designation),
        )

        data_row(
            "Joining Date",
            format_date(employee.joining_date),
        )

        status = format_status(employee.status)
        css_status = status_class(employee.status)

        st.html(
            f"""
            <div class="data-row">

                <div class="data-label">
                    Employment Status
                </div>

                <div class="data-value">
                    <span class="status-pill status-pill-{css_status}">
                        <span class="status-dot"></span>
                        {escape(status)}
                    </span>
                </div>

            </div>
            """,
        )

        st.html(
            "</div>",
        )


# ============================================================
# EMPLOYMENT INTELLIGENCE
# ============================================================

def render_employment_intelligence(
    employee: Employee,
) -> None:
    """Render employment intelligence from real employee data."""
    section_header(
        "EMPLOYMENT INTELLIGENCE",
        "Understand your current position",
        "A focused view of employment status, tenure, compensation and organizational identity.",
    )

    left, middle, right = st.columns(
        [1, 1, 1],
        gap="large",
    )

    with left:

        st.html(
            """
            <div class="panel">

                <div class="panel-title">
                    Employment Status
                </div>

                <div class="panel-description">
                    Current status from employee data
                </div>
            """,
        )

        render_status_pill(employee.status)

        st.html(
            "<br>",
        )

        data_row(
            "Joining Date",
            format_date(employee.joining_date),
        )

        data_row(
            "Current Tenure",
            calculate_tenure(employee.joining_date),
        )

        st.html(
            "</div>",
        )

    with middle:

        st.html(
            """
            <div class="panel">

                <div class="panel-title">
                    Compensation
                </div>

                <div class="panel-description">
                    Current salary recorded in your employee profile
                </div>
            """,
        )

        salary = employee.salary

        if salary is not None:

            try:
                salary_value = float(salary)

                st.html(
                    f"""
                    <div class="completion-number">
                        ₹{salary_value:,.2f}
                    </div>

                    <div class="completion-label">
                        Current recorded salary
                    </div>
                    """,
                )

                st.html(
                    "<br>",
                )

                st.info(
                    "This value is displayed from your authenticated employee record."
                )

            except (TypeError, ValueError):

                st.warning(
                    "Salary information is currently unavailable."
                )

        else:

            st.info(
                "Salary information is currently unavailable."
            )

        st.html(
            "</div>",
        )

    with right:

        st.html(
            """
            <div class="panel">

                <div class="panel-title">
                    Organizational Position
                </div>

                <div class="panel-description">
                    Your current organizational identity
                </div>
            """,
        )

        data_row(
            "Department",
            safe_text(employee.department),
        )

        data_row(
            "Designation",
            safe_text(employee.designation),
        )

        data_row(
            "Employee ID",
            safe_text(employee.employee_id),
        )

        st.html(
            "</div>",
        )


# ============================================================
# PROFILE QUALITY
# ============================================================

def render_profile_quality(
    employee: Employee,
) -> None:
    """Render dynamic profile completeness."""
    section_header(
        "DATA QUALITY",
        "Profile completeness",
        "Completeness is calculated from the real employee fields currently available to the dashboard.",
    )

    completed, total, percentage = calculate_profile_completeness(
        employee
    )

    left, right = st.columns(
        [1, 2],
        gap="large",
    )

    with left:

        st.html(
            f"""
            <div class="panel">

                <div class="completion-number">
                    {percentage}%
                </div>

                <div class="completion-label">
                    Profile completeness
                </div>

                <div class="completion-track">
                    <div
                        class="completion-fill"
                        style="width: {percentage}%"
                    ></div>
                </div>

                <br>

                <div class="completion-label">
                    {completed} of {total} available profile fields populated
                </div>

            </div>
            """,
        )

    with right:

        st.html(
            """
            <div class="panel">

                <div class="panel-title">
                    Data quality status
                </div>

                <div class="panel-description">
                    Review your employee information and contact HR if any
                    information is missing or incorrect.
            """,
        )

        if percentage == 100:

            st.success(
                "Your current employee profile contains all dashboard fields."
            )

        else:

            st.warning(
                "Some employee information is incomplete. "
                "Please contact HR for corrections."
            )

        data_row(
            "Employee Identity",
            (
                "Available"
                if employee.employee_id
                else "Missing"
            ),
        )

        data_row(
            "Contact Information",
            (
                "Available"
                if employee.email and employee.phone
                else "Incomplete"
            ),
        )

        data_row(
            "Employment Information",
            (
                "Available"
                if (
                    employee.department
                    and employee.designation
                    and employee.joining_date
                )
                else "Incomplete"
            ),
        )

        st.html(
            "</div>",
        )


# ============================================================
# REAL ACCOUNT TIMELINE
# ============================================================

def render_timeline_content(
    employee: Employee,
    user: User,
) -> None:
    """Render timeline content without adding another section wrapper."""

    events: list[
        tuple[
            datetime | date,
            str,
            str,
        ]
    ] = []

    if employee.joining_date:

        events.append(
            (
                employee.joining_date,
                "Employment Started",
                (
                    "Joining date recorded for this employee profile."
                ),
            )
        )

    if user.created_at:

        events.append(
            (
                user.created_at,
                "Portal Account Created",
                (
                    "Your employee portal account was created."
                ),
            )
        )

    if user.updated_at:

        events.append(
            (
                user.updated_at,
                "Account Record Updated",
                (
                    "Your user account record was last updated."
                ),
            )
        )

    events.sort(
        key=lambda item: item[0],
    )

    if not events:

        st.info(
            "No account timeline dates are currently available."
        )
        return

    timeline_html = (
        '<div class="panel">'
        '<div class="timeline">'
    )

    for event_date, title, description in events:

        if isinstance(event_date, datetime):

            display_date = format_datetime(
                event_date
            )

        else:

            display_date = format_date(
                event_date
            )

        timeline_html += f"""
            <div class="timeline-entry">

                <div class="timeline-dot"></div>

                <div class="timeline-date">
                    {escape(display_date)}
                </div>

                <div class="timeline-title">
                    {escape(title)}
                </div>

                <div class="timeline-text">
                    {escape(description)}
                </div>

            </div>
        """

    timeline_html += (
        "</div>"
        "</div>"
    )

    st.html(
        timeline_html,
    )


# ============================================================
# ACCOUNT & SECURITY
# ============================================================

def render_account_security(
    employee: Employee,
    user: User,
) -> None:
    """Render safe account and security information."""
    section_header(
        "ACCOUNT",
        "Account & security information",
        "Security-related information for the currently authenticated employee account.",
    )

    left, right = st.columns(
        [1, 1],
        gap="large",
    )

    with left:

        st.html(
            """
            <div class="panel">

                <div class="panel-title">
                    Login Identity
                </div>

                <div class="panel-description">
                    Information associated with your portal account
                </div>
            """,
        )

        data_row(
            "Username",
            safe_text(user.username),
        )

        data_row(
            "Login Email",
            safe_text(user.email),
        )

        data_row(
            "System Role",
            "Employee",
        )

        data_row(
            "Linked Employee",
            safe_text(employee.employee_id),
        )

        st.html(
            "</div>",
        )

    with right:

        st.html(
            """
            <div class="panel">

                <div class="panel-title">
                    Account Status
                </div>

                <div class="panel-description">
                    Current authentication and account state
                </div>
            """,
        )

        st.html(
            """
            <div class="security-item">

                <div class="security-label">
                    Authentication
                </div>

                <div class="security-value">
                    Authenticated
                </div>

            </div>
            """,
        )

        account_status = (
            "Active"
            if user.is_active
            else "Inactive"
        )

        st.html(
            f"""
            <div class="security-item">

                <div class="security-label">
                    Account Status
                </div>

                <div class="security-value">
                    {escape(account_status)}
                </div>

            </div>
            """,
        )

        st.html(
            f"""
            <div class="security-item">

                <div class="security-label">
                    Account Created
                </div>

                <div class="security-value">
                    {escape(format_datetime(user.created_at))}
                </div>

            </div>
            """,
        )

        st.html(
            f"""
            <div class="security-item">

                <div class="security-label">
                    Last Account Update
                </div>

                <div class="security-value">
                    {escape(format_datetime(user.updated_at))}
                </div>

            </div>
            """,
        )

        st.html(
            "</div>",
        )


# ============================================================
# WORKSPACE DATA TOOLS
# ============================================================

def build_employee_snapshot(employee: Employee, user: User) -> dict[str, object]:
    """Build a read-only export snapshot for the authenticated employee only."""
    return {
        "employee_id": raw_text(employee.employee_id),
        "first_name": raw_text(employee.first_name),
        "last_name": raw_text(employee.last_name),
        "full_name": full_name(employee),
        "email": raw_text(employee.email),
        "phone": raw_text(employee.phone),
        "department": raw_text(employee.department),
        "designation": raw_text(employee.designation),
        "joining_date": format_date(employee.joining_date),
        "salary": str(employee.salary) if employee.salary is not None else "",
        "status": format_status(employee.status),
        "username": raw_text(user.username),
        "role": raw_text(user.role, "employee"),
        "account_active": bool(user.is_active),
        "account_created": format_datetime(user.created_at),
        "account_updated": format_datetime(user.updated_at),
    }


def build_csv_export(snapshot: dict[str, object]) -> bytes:
    """Serialize the authenticated employee snapshot as CSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Field", "Value"])
    for key, value in snapshot.items():
        writer.writerow([key, value])
    return buffer.getvalue().encode("utf-8")


def build_vcard_export(employee: Employee) -> bytes:
    """Build a simple contact card from real employee contact data."""
    name = full_name(employee).replace("\n", " ").replace(";", " ")
    email = raw_text(employee.email).replace("\n", "")
    phone = raw_text(employee.phone).replace("\n", "")
    department = raw_text(employee.department).replace("\n", " ").replace(";", " ")
    designation = raw_text(employee.designation).replace("\n", " ").replace(";", " ")
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{name}",
        f"N:{raw_text(employee.last_name)};{raw_text(employee.first_name)};;;",
    ]
    if email:
        lines.append(f"EMAIL:{email}")
    if phone:
        lines.append(f"TEL:{phone}")
    if designation:
        lines.append(f"TITLE:{designation}")
    if department:
        lines.append(f"ORG:{department}")
    if raw_text(employee.employee_id):
        lines.append(f"NOTE:Employee ID {raw_text(employee.employee_id)}")
    lines.append("END:VCARD")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")



def build_html_report(employee: Employee, user: User) -> bytes:
    """Build a self-contained HTML report from the authenticated employee record."""
    snapshot = build_employee_snapshot(employee, user)
    rows = "".join(
        f"<tr><th>{escape(str(key).replace('_', ' ').title())}</th><td>{escape(str(value))}</td></tr>"
        for key, value in snapshot.items()
    )
    generated = datetime.now().strftime("%d %b %Y, %I:%M %p")
    html = f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>Employee Profile Report - {escape(full_name(employee))}</title>
<style>
body{{font-family:Inter,Arial,sans-serif;background:#f4f7fb;color:#0f172a;margin:0;padding:36px}}
.sheet{{max-width:920px;margin:auto;background:#fff;border:1px solid #dbe4f0;border-radius:22px;overflow:hidden;box-shadow:0 18px 50px rgba(15,23,42,.08)}}
.hero{{padding:30px 34px;background:linear-gradient(135deg,#0f172a,#1d4ed8);color:#fff}}
.kicker{{font-size:11px;letter-spacing:.14em;font-weight:800;color:#bfdbfe}}
h1{{margin:7px 0 4px;font-size:30px}} .sub{{color:#dbeafe;font-size:14px}}
.body{{padding:30px 34px}} table{{width:100%;border-collapse:collapse}} th,td{{padding:12px 10px;border-bottom:1px solid #e8eef5;text-align:left;font-size:13px}} th{{width:34%;color:#64748b;font-weight:700}} td{{font-weight:750}}
.footer{{padding:18px 34px;background:#f8fafc;color:#64748b;font-size:11px}}
</style></head><body><div class=\"sheet\"><div class=\"hero\"><div class=\"kicker\">EMPLOYEE MANAGEMENT SYSTEM</div><h1>{escape(full_name(employee))}</h1><div class=\"sub\">{escape(raw_text(employee.designation))} • {escape(raw_text(employee.department))} • Employee ID: {escape(raw_text(employee.employee_id))}</div></div><div class=\"body\"><h2>Authenticated Employee Record</h2><table>{rows}</table></div><div class=\"footer\">Generated {escape(generated)} • This report contains only the authenticated employee record.</div></div></body></html>"""
    return html.encode("utf-8")


def build_employee_package(employee: Employee, user: User) -> bytes:
    """Build a ZIP package containing the employee's real exported records."""
    snapshot = build_employee_snapshot(employee, user)
    csv_bytes = build_csv_export(snapshot)
    json_bytes = json.dumps(snapshot, indent=2, ensure_ascii=False).encode("utf-8")
    vcard_bytes = build_vcard_export(employee)
    report_bytes = build_html_report(employee, user)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("employee_profile.csv", csv_bytes)
        archive.writestr("employee_profile.json", json_bytes)
        archive.writestr("employee_contact.vcf", vcard_bytes)
        archive.writestr("employee_profile_report.html", report_bytes)
    return buffer.getvalue()


def calculate_data_freshness(employee: Employee, user: User) -> tuple[str, str]:
    """Return a human-readable freshness summary from real timestamps."""
    timestamps = [value for value in (employee.updated_at, user.updated_at) if value is not None]
    if not timestamps:
        return "Timestamp unavailable", "neutral"
    latest = max(timestamps)
    now = datetime.now(latest.tzinfo) if latest.tzinfo else datetime.now()
    age_hours = max((now - latest).total_seconds() / 3600, 0)
    if age_hours < 24:
        return "Updated within 24h", "ok"
    if age_hours < 24 * 30:
        return "Updated within 30d", "ok"
    return "Older than 30d", "warn"


def render_advanced_controls(employee: Employee, user: User) -> None:
    """Render privacy, data freshness and session diagnostics controls."""
    section_header(
        "ADVANCED CONTROLS",
        "Workspace controls & diagnostics",
        "Privacy-aware display controls and real session diagnostics for the authenticated workspace.",
    )
    left, middle, right = st.columns(3, gap="large")
    with left:
        with st.container(border=True):
            st.markdown("**Privacy center**")
            hide_salary = st.checkbox(
                "Hide salary in dashboard",
                value=st.session_state.get("employee_hide_salary", False),
                key="employee_hide_salary_control",
            )
            st.session_state["employee_hide_salary"] = hide_salary
            st.caption("This only changes on-screen visibility. Export files continue to follow the selected export scope.")
    with middle:
        freshness, tone = calculate_data_freshness(employee, user)
        with st.container(border=True):
            st.markdown("**Data freshness**")
            st.metric("Record state", freshness)
            st.caption("Based on the latest available employee/account update timestamps.")
    with right:
        with st.container(border=True):
            st.markdown("**Session diagnostics**")
            st.write(f"Role: **{raw_text(user.role, 'employee')}**")
            st.write(f"Account: **{'Active' if user.is_active else 'Inactive'}**")
            st.write(f"Employee mapping: **{'Verified' if user.employee_id == employee.id else 'Review'}**")

    with st.expander("Field-level profile audit", expanded=False):
        fields = {
            "Employee ID": employee.employee_id,
            "First name": employee.first_name,
            "Last name": employee.last_name,
            "Email": employee.email,
            "Phone": employee.phone,
            "Department": employee.department,
            "Designation": employee.designation,
            "Joining date": employee.joining_date,
            "Salary": employee.salary,
            "Status": employee.status,
        }
        audit_rows = []
        for label, value in fields.items():
            present = value is not None and str(value).strip() != ""
            audit_rows.append({"Field": label, "State": "Complete" if present else "Missing"})
        st.dataframe(audit_rows, width="stretch", hide_index=True)

def render_workspace_tools(employee: Employee, user: User) -> None:
    """Render real export and workspace package tools for the authenticated employee."""
    section_header(
        "WORKSPACE",
        "Data center & quick actions",
        "Secure tools operating only on the authenticated employee record.",
    )

    snapshot = build_employee_snapshot(employee, user)
    if st.session_state.get("employee_hide_salary", False):
        snapshot = dict(snapshot)
        snapshot["salary"] = "Hidden in dashboard"

    csv_bytes = build_csv_export(snapshot)
    json_bytes = json.dumps(snapshot, indent=2, ensure_ascii=False).encode("utf-8")
    vcard_bytes = build_vcard_export(employee)
    report_bytes = build_html_report(employee, user)
    package_bytes = build_employee_package(employee, user)

    left, middle, right = st.columns(3, gap="large")
    with left:
        st.html("""<div class=\"tool-card\"><div class=\"tool-icon\">⇩</div><div class=\"tool-title\">CSV export</div><div class=\"tool-text\">Portable tabular snapshot of your current employee record.</div></div>""")
        st.download_button("Download CSV", data=csv_bytes, file_name=f"employee_{raw_text(employee.employee_id, 'record')}.csv", mime="text/csv", width="stretch", key="employee_csv_export_v2")
    with middle:
        st.html("""<div class=\"tool-card\"><div class=\"tool-icon\">{ }</div><div class=\"tool-title\">JSON export</div><div class=\"tool-text\">Structured employee snapshot suitable for personal records.</div></div>""")
        st.download_button("Download JSON", data=json_bytes, file_name=f"employee_{raw_text(employee.employee_id, 'record')}.json", mime="application/json", width="stretch", key="employee_json_export_v2")
    with right:
        st.html("""<div class=\"tool-card\"><div class=\"tool-icon\">⌁</div><div class=\"tool-title\">Contact card</div><div class=\"tool-text\">Real contact identity in standard vCard format.</div></div>""")
        st.download_button("Download vCard", data=vcard_bytes, file_name=f"{raw_text(employee.employee_id, 'employee')}.vcf", mime="text/vcard", width="stretch", key="employee_vcard_export_v2")

    left2, right2 = st.columns(2, gap="large")
    with left2:
        st.html("""<div class=\"tool-card\"><div class=\"tool-icon\">▣</div><div class=\"tool-title\">Professional report</div><div class=\"tool-text\">Self-contained HTML profile report generated from real authenticated data.</div></div>""")
        st.download_button("Download profile report", data=report_bytes, file_name=f"employee_{raw_text(employee.employee_id, 'profile')}_report.html", mime="text/html", width="stretch", key="employee_report_export")
    with right2:
        st.html("""<div class=\"tool-card\"><div class=\"tool-icon\">▦</div><div class=\"tool-title\">Complete data package</div><div class=\"tool-text\">One ZIP containing CSV, JSON, vCard and the professional report.</div></div>""")
        st.download_button("Download complete package", data=package_bytes, file_name=f"employee_{raw_text(employee.employee_id, 'profile')}_package.zip", mime="application/zip", width="stretch", key="employee_package_export")

    with st.expander("Preview exported data", expanded=False):
        preview_columns = st.columns(2, gap="large")
        items = list(snapshot.items())
        midpoint = (len(items) + 1) // 2
        for column, group in zip(preview_columns, (items[:midpoint], items[midpoint:])):
            with column:
                for key, value in group:
                    data_row(key.replace("_", " ").title(), str(value))


# ============================================================
# EMPLOYEE SERVICES
# ============================================================

def render_service_card(
    icon: str,
    title: str,
    description: str,
) -> None:
    """Render an unavailable service without fake functionality."""
    st.html(
        f"""
        <article class="future-card">
            <div class="future-icon">
                <span class="dashboard-glyph glyph-{escape(icon)}" aria-hidden="true"></span>
            </div>

            <div class="future-title">{escape(title)}</div>

            <div class="future-status">
                <span class="dashboard-glyph glyph-lock" aria-hidden="true"></span>
                Module Not Available
            </div>

            <div class="future-text">{escape(description)}</div>
        </article>
        """,
    )


def render_services() -> None:
    """
    Render only currently unavailable service modules.

    No fake backend functionality is exposed.
    """
    section_header(
        "SELF-SERVICE",
        "Employee services",
        "Only real backend-connected services will become actionable.",
    )

    columns = st.columns(
        3,
        gap="large",
    )

    services = [
        (
            "attendance",
            "Attendance",
            (
                "Attendance history and working-day information "
                "will appear after the real attendance module is implemented."
            ),
        ),
        (
            "leave",
            "Leave Management",
            (
                "Leave balances, requests and history will become "
                "available when the real leave workflow exists."
            ),
        ),
        (
            "request",
            "HR Requests",
            (
                "Employee service requests will become actionable "
                "after the corresponding workflow is implemented."
            ),
        ),
    ]

    for index, service in enumerate(services):

        with columns[index]:
            render_service_card(
                icon=service[0],
                title=service[1],
                description=service[2],
            )


def render_employee_leaves(employee: Employee, user: User) -> None:
    section_header(
        "Leave Center & Time-off Requests",
        "Apply for leaves, track approval workflows, and check annual leave allowances.",
        "calendar",
    )

    db = SessionLocal()
    try:
        leave_svc = LeaveService(db)
        balances = leave_svc.get_leave_balance(employee.id)

        # Balances row
        b_cols = st.columns(len(balances))
        for col, (l_type, b_info) in zip(b_cols, balances.items()):
            with col:
                st.html(
                    f"""
                    <div class="emp-leave-card" style="padding:14px 18px; border-radius:14px; margin-bottom:16px;">
                        <div class="emp-leave-label" style="font-size:11px; font-weight:700; text-transform:uppercase;">{escape(l_type)}</div>
                        <div class="emp-leave-total" style="font-size:24px; font-weight:800; margin:4px 0;">{b_info['remaining']} <span class="emp-leave-sub" style="font-size:12px; font-weight:500;">/ {b_info['total']} left</span></div>
                        <div class="emp-leave-meta" style="font-size:11px;">Used: {b_info['used']} | Pending: {b_info['pending']}</div>
                    </div>
                    """
                )

        t_apply, t_history = st.tabs(["✍️ Apply for Leave", "📋 Leave History & Status"])

        with t_apply:
            with st.form("employee_apply_leave_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    sel_type = st.selectbox("Leave Type", list(LeaveService.ANNUAL_QUOTA.keys()))
                with c2:
                    start_d = st.date_input("Start Date", value=date.today())
                with c3:
                    end_d = st.date_input("End Date", value=date.today())

                reason_txt = st.text_area("Reason for Leave", placeholder="Please provide sufficient details for manager approval...")
                sub_btn = st.form_submit_button("Submit Leave Application", type="primary", width="stretch")

                if sub_btn:
                    try:
                        leave_svc.apply_leave(
                            employee_id=employee.id,
                            leave_type=sel_type,
                            start_date=start_d,
                            end_date=end_d,
                            reason=reason_txt,
                            actor_username=user.username,
                        )
                        st.success("Leave application submitted successfully. Your manager has been notified.")
                        st.rerun()
                    except ValueError as err:
                        st.error(str(err))

        with t_history:
            history = leave_svc.get_employee_leaves(employee.id)
            if not history:
                st.info("No leave requests found on your record.")
            else:
                for l in history:
                    b_color = "#f59e0b" if l.status == "Pending" else ("#10b981" if l.status == "Approved" else "#ef4444")
                    with st.container(border=True):
                        top1, top2 = st.columns([3, 1])
                        with top1:
                            st.markdown(f"**{escape(l.leave_type)}** • `{l.days_count} day(s)`")
                            st.caption(f"From {l.start_date.strftime('%d %b %Y')} to {l.end_date.strftime('%d %b %Y')} • Applied on {l.applied_at.strftime('%d %b %Y at %I:%M %p')}")
                        with top2:
                            st.html(f"<div style='text-align:right;'><span style='background:{b_color}22; color:{b_color}; border:1px solid {b_color}55; padding:4px 12px; border-radius:20px; font-weight:700; font-size:12px;'>{escape(l.status.upper())}</span></div>")

                        st.write(f"Reason: *\"{escape(l.reason)}\"*")
                        if l.admin_remarks:
                            st.caption(f"Manager Remarks: {escape(l.admin_remarks)}")

    finally:
        db.close()


def render_employee_attendance(employee: Employee, user: User) -> None:
    section_header(
        "Daily Attendance & Punch Tracker",
        "Record your daily check-in and check-out, view work hours, and monitor monthly attendance.",
        "calendar",
    )

    db = SessionLocal()
    try:
        att_svc = AttendanceService(db)
        today_stat = att_svc.get_today_status(employee.id)

        # Punch Card
        with st.container(border=True):
            st.markdown(f"### 🕒 Shift Status for {date.today().strftime('%A, %d %B %Y')}")
            col_in, col_out, col_hrs = st.columns(3)
            with col_in:
                cin = today_stat["clock_in_time"]
                st.metric("Clock In", cin.strftime("%I:%M:%S %p") if cin else "Not Checked In")
            with col_out:
                cout = today_stat["clock_out_time"]
                st.metric("Clock Out", cout.strftime("%I:%M:%S %p") if cout else ("Active Shift" if cin else "-"))
            with col_hrs:
                st.metric("Hours Worked", f"{today_stat['work_hours']:.2f} hrs")

            st.write("")
            act_col1, act_col2 = st.columns(2)

            with act_col1:
                if not today_stat["clocked_in"]:
                    punch_note = st.text_input("Daily Check-in Note (Optional)", placeholder="e.g. Working from office / remote")
                    if st.button("🕒 Clock In Now", type="primary", width="stretch"):
                        att_svc.clock_in(employee.id, notes=punch_note, actor_username=user.username)
                        st.success("Successfully clocked in!")
                        st.rerun()
                else:
                    st.success(f"✅ Clocked in at {today_stat['clock_in_time'].strftime('%I:%M %p')}")

            with act_col2:
                if today_stat["clocked_in"] and not today_stat["clocked_out"]:
                    if st.button("🛑 Clock Out (End Shift)", type="secondary", width="stretch"):
                        att_svc.clock_out(employee.id, actor_username=user.username)
                        st.info("Successfully clocked out for the day!")
                        st.rerun()
                elif today_stat["clocked_out"]:
                    st.info(f"Shift completed at {today_stat['clock_out_time'].strftime('%I:%M %p')}")

        st.write("")
        st.subheader("Monthly Attendance Log")
        records = att_svc.get_monthly_records(employee.id)
        if not records:
            st.info("No punch records for this month yet.")
        else:
            tbl = [
                {
                    "Date": r.date.strftime("%d %b %Y"),
                    "Clock In": r.clock_in.strftime("%I:%M:%S %p") if r.clock_in else "-",
                    "Clock Out": r.clock_out.strftime("%I:%M:%S %p") if r.clock_out else "-",
                    "Hours": f"{r.work_hours:.2f} hrs",
                    "Status": r.status,
                    "Notes": r.notes or "-",
                }
                for r in records
            ]
            st.dataframe(tbl, width="stretch", hide_index=True)

    finally:
        db.close()


def render_employee_payslip(employee: Employee, user: User) -> None:
    section_header(
        "My Payslip & Compensations",
        "View and download authenticated monthly salary slips with tax deductions and allowances breakdown.",
        "briefcase",
    )

    c1, c2 = st.columns(2)
    with c1:
        cur_m = date.today().month
        sel_m = st.selectbox("Select Pay Month", range(1, 13), index=cur_m - 1, format_func=lambda m: date(2026, m, 1).strftime("%B"), key="emp_ps_m")
    with c2:
        cur_y = date.today().year
        sel_y = st.number_input("Pay Year", min_value=2020, max_value=2030, value=cur_y, key="emp_ps_y")

    data = PayslipService.calculate_salary_breakdown(employee, int(sel_y), int(sel_m))
    html_slip = PayslipService.generate_html_payslip(employee, int(sel_y), int(sel_m))

    with st.container(border=True):
        st.markdown(f"### Payslip for {data['pay_period']}")
        st.caption(f"**Employee:** {data['full_name']} `({data['employee_id']})` • **Payable Days:** {data['days_payable']}")

        ec1, ec2 = st.columns(2)
        with ec1:
            st.markdown("#### 🟢 Earnings Breakdown")
            for k, v in data["earnings"].items():
                st.write(f"- **{k}:** ₹{v:,.2f}")
            st.markdown(f"**Total Gross:** `₹{data['total_earnings']:,.2f}`")

        with ec2:
            st.markdown("#### 🔴 Deductions")
            for k, v in data["deductions"].items():
                st.write(f"- **{k}:** ₹{v:,.2f}")
            st.markdown(f"**Total Deductions:** `₹{data['total_deductions']:,.2f}`")

        st.divider()
        st.html(
            f"""
            <div style="background:linear-gradient(135deg,#1e3a8a,#2563eb); color:#ffffff; padding:18px 24px; border-radius:12px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:12px; opacity:0.85; text-transform:uppercase; letter-spacing:1px;">Net Disbursed Salary</div>
                    <div style="font-size:11px; opacity:0.75;">(Credited to registered salary account)</div>
                </div>
                <div style="font-size:28px; font-weight:800;">₹{data['net_salary']:,.2f}</div>
            </div>
            """
        )

        st.write("")
        st.download_button(
            "📥 Download Formal Printable Payslip (HTML)",
            data=html_slip,
            file_name=f"payslip_{employee.employee_id}_{sel_m}_{sel_y}.html",
            mime="text/html",
            type="primary",
        )

        with st.expander("📄 View Payslip Live Document Preview"):
            st.components.v1.html(html_slip, height=600, scrolling=True)


def render_employee_announcements(employee: Employee, user: User) -> None:
    section_header(
        "Company Notice Board",
        "Official company announcements, holiday schedules, and workplace policy bulletins.",
        "search",
    )

    db = SessionLocal()
    try:
        ann_svc = AnnouncementService(db)
        active_list = ann_svc.get_active(target_role="employee")

        if not active_list:
            st.info("No active announcements at this time.")
        else:
            for a in active_list:
                tone = "urgent" if a.priority == "Urgent" else ("important" if a.priority == "Important" else "normal")
                with st.container(border=True):
                    h1, h2 = st.columns([3, 1])
                    with h1:
                        st.markdown(f"### {escape(a.title)}")
                        st.caption(f"Posted by **{escape(a.posted_by)}** on {a.created_at.strftime('%d %B %Y at %I:%M %p')}")
                    with h2:
                        badge_color = "#dc2626" if a.priority == "Urgent" else ("#d97706" if a.priority == "Important" else "#2563eb")
                        st.html(f"<div style='text-align:right;'><span style='background:{badge_color}22; color:{badge_color}; border:1px solid {badge_color}55; padding:4px 12px; border-radius:20px; font-weight:700; font-size:12px;'>{escape(a.priority.upper())}</span></div>")

                    st.markdown(a.content)
    finally:
        db.close()


# ============================================================
# FOOTER
# ============================================================

def render_footer(
    employee: Employee,
) -> None:
    """Render secure dashboard footer."""
    st.html(
        f"""
        <div class="dashboard-footer">

            Employee Management System
            &nbsp;•&nbsp;
            Authenticated Employee Portal
            &nbsp;•&nbsp;
            {escape(raw_text(employee.employee_id))}

            <br>

            Data displayed from the authenticated employee record only.

        </div>
        """,
    )


# ============================================================
# MAIN DASHBOARD
# ============================================================

def main() -> None:
    """
    Employee dashboard entry point.

    Security flow:

        Session
          ↓
        Employee role
          ↓
        User account
          ↓
        Active account
          ↓
        Employee mapping
          ↓
        One linked employee
          ↓
        Dashboard
    """

    # --------------------------------------------------------
    # ROLE PROTECTION
    # --------------------------------------------------------

    if not st.session_state.get("authenticated"):

        terminate_invalid_session(
            "Your login session is not active."
        )

        return

    if st.session_state.get("role") != "employee":

        terminate_invalid_session(
            "Access denied. Employee access is required."
        )

        return

    user_id = st.session_state.get("user_id")

    if not user_id:

        terminate_invalid_session(
            "Your login session is invalid."
        )

        return

    render_styles()
    render_navigation_styles()

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # AUTHENTICATED USER
        # ----------------------------------------------------

        user = db.get(
            User,
            user_id,
        )

        if user is None:

            terminate_invalid_session(
                "Your user account could not be found."
            )

            return

        # ----------------------------------------------------
        # ACTIVE USER CHECK
        # ----------------------------------------------------

        if not user.is_active:

            terminate_invalid_session(
                "Your account is inactive. "
                "Please contact HR or the administrator."
            )

            return

        # ----------------------------------------------------
        # EMPLOYEE MAPPING CHECK
        # ----------------------------------------------------

        if user.employee_id is None:

            terminate_invalid_session(
                "Your account is not linked to an employee profile."
            )

            return

        # ----------------------------------------------------
        # LOAD ONLY LINKED EMPLOYEE
        # ----------------------------------------------------

        employee = db.get(
            Employee,
            user.employee_id,
        )

        if employee is None:

            terminate_invalid_session(
                "Your linked employee profile could not be found."
            )

            return

        # ----------------------------------------------------
        # RENDER DASHBOARD
        # ----------------------------------------------------

        render_sidebar(
            employee,
            user,
        )

        render_hero(employee)
        render_workspace_toolbar(employee, user)

        view = get_employee_view()

        if view == "All sections":
            render_collapsible_employee_workspace(employee, user, view)
            render_employee_leaves(employee, user)
            render_employee_attendance(employee, user)
            render_employee_payslip(employee, user)
            render_employee_announcements(employee, user)
            render_workspace_tools(employee, user)
            render_data_integrity(employee, user)
            render_advanced_controls(employee, user)
            render_missing_profile_fields(employee)

        elif view == "Overview":
            render_collapsible_employee_workspace(employee, user, view)
            render_data_integrity(employee, user)

        elif view == "Leave Center":
            render_employee_leaves(employee, user)

        elif view == "Daily Attendance":
            render_employee_attendance(employee, user)

        elif view == "My Payslip":
            render_employee_payslip(employee, user)

        elif view == "Notice Board":
            render_employee_announcements(employee, user)

        elif view == "Profile & employment":
            render_profile_and_employment(employee)
            render_profile_quality(employee)
            render_missing_profile_fields(employee)

        elif view == "Security":
            render_account_security(employee, user)
            render_timeline_content(employee, user)
            render_data_integrity(employee, user)

        elif view == "Data center":
            render_workspace_tools(employee, user)
            render_advanced_controls(employee, user)
            render_data_integrity(employee, user)

        render_footer(employee)

    except Exception:

        st.error(
            "Unable to load your employee dashboard. "
            "Please contact the administrator."
        )

    finally:

        db.close()


# ============================================================
# INTERNAL COLLAPSIBLE EMPLOYEE PANEL
# ============================================================

def render_internal_employee_panel(employee: Employee, user: User) -> None:
    """Render the internal dashboard-side employee panel using real data."""
    is_open = st.session_state.get("employee_left_panel_open", True)

    if is_open:
        st.html(f"""
        <section class="internal-employee-panel">
            <div class="internal-panel-head">
                <div>
                    <span class="internal-panel-kicker">EMPLOYEE PANEL</span>
                    <h3>Employee identity</h3>
                    <p>Quick access to your verified profile.</p>
                </div>
                <div class="internal-panel-avatar">{safe_text(initials(employee))}</div>
            </div>

            <div class="internal-identity">
                <strong>{safe_text(full_name(employee))}</strong>
                <span>{safe_text(employee.email)}</span>
            </div>

            <div class="internal-data-row">
                <span>Employee ID</span>
                <strong>{safe_text(employee.employee_id)}</strong>
            </div>
            <div class="internal-data-row">
                <span>Department</span>
                <strong>{safe_text(employee.department)}</strong>
            </div>
            <div class="internal-data-row">
                <span>Designation</span>
                <strong>{safe_text(employee.designation)}</strong>
            </div>
            <div class="internal-data-row">
                <span>Status</span>
                <strong>{safe_text(format_status(employee.status))}</strong>
            </div>

            <div class="internal-panel-note">
                <span class="internal-panel-note-icon">✓</span>
                <div>
                    <strong>Verified session</strong>
                    <span>Authenticated employee access</span>
                </div>
            </div>
        </section>
        """)

        if st.button(
            "◀  Hide employee panel",
            key="employee_hide_internal_panel",
            width="stretch",
            type="secondary",
        ):
            st.session_state["employee_left_panel_open"] = False
            st.rerun()
    else:
        if st.button(
            "▶",
            key="employee_show_internal_panel",
            help="Show employee panel",
            width="stretch",
            type="secondary",
        ):
            st.session_state["employee_left_panel_open"] = True
            st.rerun()


def render_collapsible_employee_workspace(
    employee: Employee,
    user: User,
    view: str,
) -> None:
    """Render the dashboard with a collapsible internal left panel."""
    if "employee_left_panel_open" not in st.session_state:
        st.session_state["employee_left_panel_open"] = True

    is_open = st.session_state["employee_left_panel_open"]

    if is_open:
        left_col, main_col = st.columns([0.27, 0.73], gap="large")
        with left_col:
            render_internal_employee_panel(employee, user)
        with main_col:
            if view == "All sections":
                render_premium_command_center(employee, user)
            else:
                render_premium_command_center(employee, user)
    else:
        control_col, main_col = st.columns([0.055, 0.945], gap="small")
        with control_col:
            render_internal_employee_panel(employee, user)
        with main_col:
            render_premium_command_center(employee, user)

# ============================================================
# PREMIUM COMMAND CENTER
# ============================================================

def render_premium_command_center(employee: Employee, user: User) -> None:
    """Render a compact, executive-style employee command center using real data."""
    completed, total, percentage = calculate_profile_completeness(employee)
    tenure = calculate_tenure(employee.joining_date)
    status = format_status(employee.status)
    salary = employee.salary
    salary_text = "Not available"
    if salary is not None:
        try:
            salary_text = f"₹{float(salary):,.0f}"
        except (TypeError, ValueError):
            salary_text = "Not available"

    if st.session_state.get("employee_hide_salary", False):
        salary_text = "Hidden"

    st.html(f"""
    <section class="premium-command-center">
        <div class="command-topline">
            <div>
                <div class="command-kicker">EMPLOYEE COMMAND CENTER</div>
                <div class="command-heading">Your work profile, organized.</div>
                <div class="command-subtitle">A real-time view built from your authenticated employee and account records.</div>
            </div>
            <div class="command-context">
                <span class="command-context-icon"><span class="dashboard-glyph glyph-shield"></span></span>
                <span><strong>Verified session</strong><small>Employee access</small></span>
            </div>
        </div>

        <div class="command-metrics">
            <div class="command-metric">
                <div class="metric-icon"><span class="dashboard-glyph glyph-id"></span></div>
                <div><small>EMPLOYEE ID</small><strong>{safe_text(employee.employee_id)}</strong></div>
            </div>
            <div class="command-metric">
                <div class="metric-icon"><span class="dashboard-glyph glyph-tenure"></span></div>
                <div><small>TENURE</small><strong>{safe_text(tenure)}</strong></div>
            </div>
            <div class="command-metric">
                <div class="metric-icon"><span class="dashboard-glyph glyph-briefcase"></span></div>
                <div><small>POSITION</small><strong>{safe_text(employee.designation)}</strong></div>
            </div>
            <div class="command-metric">
                <div class="metric-icon"><span class="dashboard-glyph glyph-shield"></span></div>
                <div><small>PROFILE QUALITY</small><strong>{percentage}%</strong></div>
            </div>
        </div>
    </section>
    """)

    st.html(f"""
    <div class="advanced-grid two-up">
        <section class="advanced-panel">
            <div class="advanced-panel-head">
                <div>
                    <span class="advanced-kicker">IDENTITY</span>
                    <h3>Personal profile</h3>
                    <p>Core information from your employee record.</p>
                </div>
                <div class="panel-icon"><span class="dashboard-glyph glyph-profile"></span></div>
            </div>
            <div class="identity-banner">
                <div class="identity-avatar">{safe_text(initials(employee))}</div>
                <div><strong>{safe_text(full_name(employee))}</strong><span>{safe_text(employee.email)}</span></div>
            </div>
            <div class="advanced-data-grid">
                <div><small>First name</small><strong>{safe_text(employee.first_name)}</strong></div>
                <div><small>Last name</small><strong>{safe_text(employee.last_name)}</strong></div>
                <div><small>Email</small><strong>{safe_text(employee.email)}</strong></div>
                <div><small>Phone</small><strong>{safe_text(employee.phone)}</strong></div>
            </div>
        </section>

        <section class="advanced-panel">
            <div class="advanced-panel-head">
                <div>
                    <span class="advanced-kicker">EMPLOYMENT</span>
                    <h3>Current position</h3>
                    <p>Organizational information currently recorded for you.</p>
                </div>
                <div class="panel-icon"><span class="dashboard-glyph glyph-briefcase"></span></div>
            </div>
            <div class="position-highlight">
                <div><small>DESIGNATION</small><strong>{safe_text(employee.designation)}</strong></div>
                <div class="status-chip"><span></span>{safe_text(status)}</div>
            </div>
            <div class="advanced-data-grid">
                <div><small>Department</small><strong>{safe_text(employee.department)}</strong></div>
                <div><small>Employee ID</small><strong>{safe_text(employee.employee_id)}</strong></div>
                <div><small>Joining date</small><strong>{format_date(employee.joining_date)}</strong></div>
                <div><small>Salary</small><strong>{safe_text(salary_text)}</strong></div>
            </div>
        </section>
    </div>

    <div class="advanced-grid three-up">
        <article class="insight-card">
            <div class="insight-icon"><span class="dashboard-glyph glyph-shield"></span></div>
            <div><small>EMPLOYMENT STATUS</small><strong>{safe_text(status)}</strong><p>Current status from your employee record.</p></div>
        </article>
        <article class="insight-card">
            <div class="insight-icon"><span class="dashboard-glyph glyph-tenure"></span></div>
            <div><small>JOINED</small><strong>{format_date(employee.joining_date)}</strong><p>{safe_text(tenure)} of recorded tenure.</p></div>
        </article>
        <article class="insight-card">
            <div class="insight-icon"><span class="dashboard-glyph glyph-profile"></span></div>
            <div><small>DATA QUALITY</small><strong>{percentage}% complete</strong><p>{completed} of {total} dashboard fields populated.</p></div>
        </article>
    </div>
    """)

    left, right = st.columns([1.05, 1.45], gap="large")
    with left:
        st.html(f"""
        <section class="advanced-panel quality-panel">
            <div class="advanced-panel-head"><div><span class="advanced-kicker">DATA QUALITY</span><h3>Profile health</h3><p>Completeness calculated from real employee fields.</p></div><div class="panel-icon"><span class="dashboard-glyph glyph-shield"></span></div></div>
            <div class="quality-score"><strong>{percentage}%</strong><span>profile completeness</span></div>
            <div class="quality-track"><span style="width:{percentage}%"></span></div>
            <div class="quality-foot"><span>{completed}/{total} fields populated</span><span>{'Healthy' if percentage == 100 else 'Needs review'}</span></div>
        </section>
        """)
    with right:
        st.html(f"""
        <section class="advanced-panel security-panel">
            <div class="advanced-panel-head"><div><span class="advanced-kicker">ACCOUNT SECURITY</span><h3>Access & account state</h3><p>Read-only information for the authenticated account.</p></div><div class="panel-icon"><span class="dashboard-glyph glyph-lock"></span></div></div>
            <div class="security-grid">
                <div><small>USERNAME</small><strong>{safe_text(user.username)}</strong></div>
                <div><small>ROLE</small><strong>Employee</strong></div>
                <div><small>ACCOUNT STATUS</small><strong>{'Active' if user.is_active else 'Inactive'}</strong></div>
                <div><small>LAST UPDATED</small><strong>{format_datetime(user.updated_at)}</strong></div>
            </div>
        </section>
        """)

    section_header("ACCOUNT HISTORY", "Your timeline", "Important dates available from the real employee and user records.")
    render_timeline_content(employee, user)

# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":
    main()