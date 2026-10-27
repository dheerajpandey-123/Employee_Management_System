import pytest
from streamlit.testing.v1 import AppTest
from app.ui.theme import get_theme_css


def test_theme_initialization():
    at = AppTest.from_file("main.py")
    at.run(timeout=30)
    assert at.session_state["theme"] == "dark"


def test_theme_switch_admin():
    at = AppTest.from_file("main.py")
    at.session_state["authenticated"] = True
    at.session_state["user_id"] = 1
    at.session_state["username"] = "admin123"
    at.session_state["role"] = "admin"
    at.run(timeout=30)
    assert at.session_state["theme"] == "dark"
    assert len(at.exception) == 0

    # Toggle to light mode via the sidebar toggle widget
    assert len(at.sidebar.toggle) > 0
    at.sidebar.toggle[0].set_value(False).run(timeout=30)
    assert at.session_state["theme"] == "light"
    assert len(at.exception) == 0


def test_theme_css_light_mode_has_black_text():
    light_css = get_theme_css("light")
    # Must enforce black/dark text on white/light backgrounds
    assert "#0f172a !important" in light_css
    assert "#000000 !important" in light_css
    assert "[data-testid=\"stTextInput\"] input" in light_css
    assert "[data-testid=\"stWidgetLabel\"] label" in light_css
    assert "table" in light_css


def test_theme_css_dark_mode_has_bright_visible_text():
    dark_css = get_theme_css("dark")
    # Must enforce bright white text on dark backgrounds
    assert "#ffffff !important" in dark_css
    assert "#f8fafc !important" in dark_css
    assert "#94a3b8 !important" in dark_css


def test_theme_switch_hr():
    at = AppTest.from_file("main.py")
    at.session_state["authenticated"] = True
    at.session_state["user_id"] = 3
    at.session_state["username"] = "hr_manager"
    at.session_state["role"] = "hr"
    at.run(timeout=30)
    assert at.session_state["theme"] == "dark"
    assert len(at.exception) == 0

    # Toggle to light mode in HR
    assert len(at.sidebar.toggle) > 0
    at.sidebar.toggle[0].set_value(False).run(timeout=30)
    assert at.session_state["theme"] == "light"
    assert len(at.exception) == 0


def test_theme_switch_employee():
    at = AppTest.from_file("main.py")
    at.session_state["authenticated"] = True
    at.session_state["user_id"] = 2
    at.session_state["username"] = "emp001"
    at.session_state["role"] = "employee"
    at.run(timeout=30)
    assert at.session_state["theme"] == "dark"
    assert len(at.exception) == 0

    # Toggle to light mode in Employee dashboard
    assert len(at.toggle) > 0
    at.toggle[0].set_value(False).run(timeout=30)
    assert at.session_state["theme"] == "light"
    assert len(at.exception) == 0
