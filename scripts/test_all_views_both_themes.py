import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from streamlit.testing.v1 import AppTest

def test_everything():
    themes = ["dark", "light"]

    # 1. Login page
    for t in themes:
        at = AppTest.from_file("main.py")
        at.session_state["authenticated"] = False
        at.session_state["theme"] = t
        at.run(timeout=30)
        assert len(at.exception) == 0, f"Login failed in {t} theme: {[e.value for e in at.exception]}"
        print(f"[OK] Login page passed in {t} mode")

    # 2. Admin dashboard pages
    admin_pages = [
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
    for t in themes:
        for p in admin_pages:
            at = AppTest.from_file("main.py")
            at.session_state["authenticated"] = True
            at.session_state["user_id"] = 1
            at.session_state["username"] = "admin123"
            at.session_state["role"] = "admin"
            at.session_state["selected_page"] = p
            at.session_state["theme"] = t
            at.run(timeout=30)
            assert len(at.exception) == 0, f"Admin [{p}] failed in {t} theme: {[e.value for e in at.exception]}"
        print(f"[OK] All {len(admin_pages)} Admin pages passed in {t} mode")

    # 3. HR dashboard pages
    hr_pages = [
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
    ]
    for t in themes:
        for p in hr_pages:
            at = AppTest.from_file("main.py")
            at.session_state["authenticated"] = True
            at.session_state["user_id"] = 3
            at.session_state["username"] = "hr_manager"
            at.session_state["role"] = "hr"
            at.session_state["hr_navigation"] = p
            at.session_state["theme"] = t
            at.run(timeout=30)
            assert len(at.exception) == 0, f"HR [{p}] failed in {t} theme: {[e.value for e in at.exception]}"
        print(f"[OK] All {len(hr_pages)} HR pages passed in {t} mode")

    # 4. Employee dashboard views
    emp_views = [
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
    for t in themes:
        for v in emp_views:
            at = AppTest.from_file("main.py")
            at.session_state["authenticated"] = True
            at.session_state["user_id"] = 2
            at.session_state["username"] = "emp001"
            at.session_state["role"] = "employee"
            at.session_state["employee_view"] = v
            at.session_state["theme"] = t
            at.run(timeout=30)
            assert len(at.exception) == 0, f"Employee [{v}] failed in {t} theme: {[e.value for e in at.exception]}"
        print(f"[OK] All {len(emp_views)} Employee views passed in {t} mode")

    print("\n[SUCCESS] ALL PAGES AND VIEWS PASSED IN BOTH DARK AND LIGHT MODES WITH ZERO EXCEPTIONS!")

if __name__ == "__main__":
    test_everything()
