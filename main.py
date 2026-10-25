import streamlit as st

from app.ui.dashboard import main as admin_dashboard_main
from app.ui.employee_dashboard import main as employee_dashboard_main
from app.ui.hr_dashboard import main as hr_dashboard_main
from app.ui.login import render_login_page


def initialize_session() -> None:
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None

    if "username" not in st.session_state:
        st.session_state["username"] = None

    if "role" not in st.session_state:
        st.session_state["role"] = None

    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"


def render_role_dashboard() -> None:
    role = st.session_state.get("role")

    if role == "admin":
        admin_dashboard_main()
    elif role == "hr":
        hr_dashboard_main()
    elif role == "employee":
        employee_dashboard_main()
    else:
        st.error("Invalid user role. Please log in again.")

        st.session_state["authenticated"] = False
        st.session_state["user_id"] = None
        st.session_state["username"] = None
        st.session_state["role"] = None

        st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="Employee Management System",
        page_icon="👥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    initialize_session()

    if not st.session_state["authenticated"]:
        render_login_page()
        return

    render_role_dashboard()


if __name__ == "__main__":
    main()