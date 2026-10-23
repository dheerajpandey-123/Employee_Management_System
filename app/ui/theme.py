import streamlit as st


def get_theme_css(theme: str = "dark") -> str:
    """
    Generate unified, accessible, ultra-high contrast CSS for both Light and Dark modes.
    Guarantees:
      - The SIDEBAR is ALWAYS dark navy with 100% visible, bright white and silver text
        in BOTH Light Mode and Dark Mode (navigation items, headers, titles, toggles, expanders).
      - In Light Mode (White Dashboard): ALL main content text is deep black/dark slate (#0f172a / #000000),
        100% visible on white cards, inputs, tables, widgets, and backgrounds.
      - In Dark Mode (Dark Dashboard): ALL main content text is bright white/light slate (#ffffff / #f8fafc / #94a3b8),
        100% visible on dark navy/slate cards, inputs, tables, widgets, and backgrounds.
    """
    is_dark = (theme == "dark")

    sidebar_css = """
    /* ========================================================
       SIDEBAR - PERMANENT ULTRA HIGH-CONTRAST DARK NAVY LUXURY THEME
       Always dark navy with bright white, silver, and light blue text!
       Prevents any dark text bleed into the sidebar in all modes.
       ======================================================== */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #070e24 0%, #0b1736 50%, #08112b 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.09) !important;
    }

    /* All Titles & Strong Elements in Sidebar */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] strong,
    section[data-testid="stSidebar"] b,
    section[data-testid="stSidebar"] .sidebar-brand-name,
    section[data-testid="stSidebar"] .side-brand-title,
    section[data-testid="stSidebar"] .side-profile-name,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] b {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    /* All Paragraphs, Divs, Spans, Labels in Sidebar */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
        color: #e2e8f0 !important;
    }

    /* Sidebar Section Headings (APPEARANCE, WORKSPACE, etc.) */
    section[data-testid="stSidebar"] .sidebar-section-label,
    section[data-testid="stSidebar"] .side-brand-subtitle,
    section[data-testid="stSidebar"] .sidebar-brand-subtitle,
    section[data-testid="stSidebar"] .side-account-label,
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: #93c5fd !important;
        font-weight: 800 !important;
        letter-spacing: 1.5px !important;
        font-size: 10px !important;
        text-transform: uppercase !important;
    }

    /* Sidebar Navigation Items (Radio Buttons) */
    section[data-testid="stSidebar"] [data-testid="stRadio"] {
        background: transparent !important;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] label,
    section[data-testid="stSidebar"] [data-testid="stRadio"] label p,
    section[data-testid="stSidebar"] [data-testid="stRadio"] label span,
    section[data-testid="stSidebar"] [data-testid="stRadio"] label div {
        color: #f1f5f9 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(div[role="radio"][aria-checked="true"]),
    section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {
        background: linear-gradient(90deg, rgba(79, 109, 245, 0.35), rgba(124, 92, 255, 0.20)) !important;
        border: 1px solid rgba(129, 140, 248, 0.4) !important;
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(div[role="radio"][aria-checked="true"]) p,
    section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(div[role="radio"][aria-checked="true"]) span {
        color: #ffffff !important;
        font-weight: 750 !important;
    }

    /* Sidebar Toggle (Theme Switcher) */
    section[data-testid="stSidebar"] [data-testid="stToggle"] label,
    section[data-testid="stSidebar"] [data-testid="stToggle"] p,
    section[data-testid="stSidebar"] [data-testid="stToggle"] span {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }

    /* Sidebar Expanders (Must be dark slate, NEVER white!) */
    section[data-testid="stSidebar"] [data-testid="stExpander"] {
        background: #0f1c39 !important;
        border: 1px solid rgba(148, 163, 184, 0.22) !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
        margin-bottom: 12px !important;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] details summary {
        background: #15254a !important;
        color: #ffffff !important;
        font-weight: 750 !important;
        border-radius: 14px !important;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] details summary * {
        color: #ffffff !important;
        font-weight: 750 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] details summary svg {
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
        background: #0f1c39 !important;
        color: #f1f5f9 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] * {
        color: #f1f5f9 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] strong,
    section[data-testid="stSidebar"] [data-testid="stExpander"] b {
        color: #ffffff !important;
    }

    /* Sidebar Brand & Profile Cards */
    section[data-testid="stSidebar"] .sidebar-brand,
    section[data-testid="stSidebar"] .side-brand,
    section[data-testid="stSidebar"] .side-profile {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03)) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 16px !important;
    }

    section[data-testid="stSidebar"] .sidebar-brand *,
    section[data-testid="stSidebar"] .side-brand *,
    section[data-testid="stSidebar"] .side-profile * {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .sidebar-brand-subtitle,
    section[data-testid="stSidebar"] .side-brand-subtitle,
    section[data-testid="stSidebar"] .side-profile-id {
        color: #94a3b8 !important;
    }

    /* HR Sidebar Box */
    section[data-testid="stSidebar"] div[style*="HR COMMAND CENTER"] {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] div[style*="SIGNED IN AS"] {
        color: #94a3b8 !important;
    }

    /* Sidebar Status & Footer */
    section[data-testid="stSidebar"] .sidebar-status {
        border: 1px solid rgba(74, 222, 128, 0.2) !important;
        background: rgba(74, 222, 128, 0.08) !important;
    }

    section[data-testid="stSidebar"] .sidebar-status-title {
        color: #86efac !important;
        font-weight: 750 !important;
    }

    section[data-testid="stSidebar"] .sidebar-status-text,
    section[data-testid="stSidebar"] .sidebar-footer-title {
        color: #94a3b8 !important;
    }

    section[data-testid="stSidebar"] .sidebar-footer-text {
        color: #64748b !important;
    }

    /* Sidebar Action Buttons */
    section[data-testid="stSidebar"] [data-testid="stButton"] button {
        background: rgba(255, 255, 255, 0.07) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #f8fafc !important;
        font-weight: 700 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
        background: rgba(255, 255, 255, 0.14) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        color: #ffffff !important;
    }
    """

    if is_dark:
        main_css = """
        /* ========================================================
           MAIN CONTENT AREA - DARK DASHBOARD (MAXIMUM VISIBILITY)
           Bright white & crisp silver text on dark surfaces
           ======================================================== */
        section.main,
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        .stApp:not([data-testid="stSidebar"]) {
            background:
                radial-gradient(900px 500px at 5% 0%, rgba(99, 102, 241, 0.15), transparent 65%),
                radial-gradient(700px 500px at 100% 100%, rgba(14, 165, 233, 0.10), transparent 65%),
                #080c16 !important;
            color: #f8fafc !important;
        }

        /* Headings */
        section.main h1,
        section.main h2,
        section.main h3,
        section.main h4,
        section.main h5,
        section.main h6,
        section.main .page-title,
        section.main .section-heading,
        section.main .section-title,
        section.main .hr-hero-title,
        section.main .profile-name,
        section.main .login-title,
        section.main .brand-title {
            color: #ffffff !important;
            font-weight: 800 !important;
        }

        /* Body & Elements */
        section.main p,
        section.main span,
        section.main div,
        section.main li,
        section.main strong,
        section.main b,
        section.main em,
        section.main label,
        section.main dt,
        section.main dd {
            color: #f8fafc !important;
        }

        section.main .page-subtitle,
        section.main .section-subtitle,
        section.main .v8-eyebrow,
        section.main .page-eyebrow,
        section.main .brand-kicker,
        section.main .login-description,
        section.main .brand-description,
        section.main small,
        section.main caption,
        section.main [data-testid="stCaptionContainer"],
        section.main [data-testid="stCaptionContainer"] p,
        section.main .v8-kpi-note,
        section.main .metric-description,
        section.main .metric-note,
        section.main .v8-role-info span,
        section.main .v8-employee-cell span,
        section.main .muted,
        section.main .text-muted,
        section.main .advanced-panel-head p,
        section.main .identity-banner span,
        section.main .insight-card p,
        section.main .quality-score span,
        section.main .login-trust span,
        section.main .brand-footer,
        section.main .trust-label {
            color: #94a3b8 !important;
        }

        /* Markdown Container */
        section.main [data-testid="stMarkdownContainer"] * {
            color: #f8fafc !important;
        }

        section.main [data-testid="stMarkdownContainer"] strong,
        section.main [data-testid="stMarkdownContainer"] b {
            color: #ffffff !important;
            font-weight: 800 !important;
        }

        section.main [data-testid="stMarkdownContainer"] code {
            background: #1e293b !important;
            color: #818cf8 !important;
            border: 1px solid rgba(148, 163, 184, 0.25) !important;
            border-radius: 6px !important;
            padding: 2px 6px !important;
        }

        /* Form Labels */
        section.main [data-testid="stWidgetLabel"] label,
        section.main [data-testid="stWidgetLabel"] p,
        section.main [data-testid="stWidgetLabel"] * {
            color: #f8fafc !important;
            font-weight: 700 !important;
            font-size: 13px !important;
        }

        /* Inputs */
        section.main [data-testid="stTextInput"] input,
        section.main [data-testid="stNumberInput"] input,
        section.main [data-testid="stDateInput"] input,
        section.main [data-testid="stTextArea"] textarea {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1.5px solid rgba(148, 163, 184, 0.28) !important;
            border-radius: 10px !important;
            font-weight: 500 !important;
            font-size: 14px !important;
        }

        section.main input::placeholder,
        section.main textarea::placeholder {
            color: #94a3b8 !important;
            opacity: 1 !important;
        }

        /* Selectboxes */
        section.main [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1.5px solid rgba(148, 163, 184, 0.28) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }

        section.main [data-testid="stSelectbox"] div[data-baseweb="select"] * {
            color: #f8fafc !important;
        }

        div[data-baseweb="popover"],
        ul[role="listbox"],
        li[role="option"] {
            background: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid rgba(148, 163, 184, 0.3) !important;
        }

        li[role="option"]:hover,
        li[role="option"][aria-selected="true"] {
            background: #334155 !important;
            color: #ffffff !important;
        }

        /* Forms */
        section.main [data-testid="stForm"],
        section.main div[data-testid="stForm"] {
            background: #0f172a !important;
            border: 1px solid rgba(148, 163, 184, 0.18) !important;
            border-radius: 16px !important;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35) !important;
        }

        /* Cards, Panels, Containers */
        section.main .v8-panel,
        section.main .v8-kpi,
        section.main .v8-mini-card,
        section.main .v8-table-panel,
        section.main .metric-card,
        section.main .panel,
        section.main .kpi-card,
        section.main .panel-card,
        section.main .workspace-panel,
        section.main [data-testid="stVerticalBlockBorderWrapper"],
        section.main .advanced-panel,
        section.main .insight-card,
        section.main .ems-announcement-card,
        section.main .ems-stat-chip,
        section.main .profile-card,
        section.main .profile-item,
        section.main .emp-leave-card {
            background: #0f172a !important;
            border: 1px solid rgba(148, 163, 184, 0.18) !important;
            color: #f8fafc !important;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45) !important;
        }

        section.main .v8-kpi-value,
        section.main .kpi-value,
        section.main .metric-value,
        section.main .v8-mini-body strong,
        section.main .v8-data-row-top strong,
        section.main .v8-role-info strong,
        section.main .v8-employee-cell strong,
        section.main .ems-stat-chip strong,
        section.main .emp-leave-total,
        section.main .advanced-panel-head h3,
        section.main .identity-banner strong,
        section.main .advanced-data-grid strong,
        section.main .position-highlight strong,
        section.main .insight-card strong,
        section.main .quality-score strong,
        section.main .trust-value,
        section.main .brand-product,
        section.main [data-testid="stMetricValue"] * {
            color: #ffffff !important;
            font-weight: 850 !important;
        }

        section.main .v8-kpi-label,
        section.main .kpi-label,
        section.main .metric-label,
        section.main .v8-mini-body span,
        section.main .v8-data-row-top span,
        section.main .v8-role-info span,
        section.main .v8-employee-cell span,
        section.main .emp-leave-label,
        section.main .emp-leave-sub,
        section.main [data-testid="stMetricLabel"] * {
            color: #94a3b8 !important;
            font-weight: 700 !important;
        }

        section.main .emp-leave-meta {
            color: #38bdf8 !important;
            font-weight: 600 !important;
        }

        section.main .identity-banner,
        section.main .position-highlight {
            background: #1e293b !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
        }

        /* Expanders in Main Area */
        section.main [data-testid="stExpander"] {
            background: #0f172a !important;
            border: 1px solid rgba(148, 163, 184, 0.18) !important;
            border-radius: 14px !important;
        }

        section.main [data-testid="stExpander"] details summary {
            background: #1e293b !important;
            color: #ffffff !important;
            font-weight: 750 !important;
            border-radius: 14px !important;
        }

        section.main [data-testid="stExpander"] details summary * {
            color: #ffffff !important;
            font-weight: 750 !important;
        }

        section.main [data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
            background: #0f172a !important;
            color: #f8fafc !important;
        }

        /* Tabs in Main Area */
        section.main [data-testid="stTabs"] button {
            color: #94a3b8 !important;
            font-weight: 650 !important;
            font-size: 14px !important;
        }

        section.main [data-testid="stTabs"] button[aria-selected="true"] {
            color: #818cf8 !important;
            font-weight: 800 !important;
            border-bottom: 2.5px solid #818cf8 !important;
        }

        /* Tables & DataFrames */
        section.main table {
            background: #0f172a !important;
            color: #f8fafc !important;
        }

        section.main th,
        section.main .v8-table th {
            background: #1e293b !important;
            color: #e2e8f0 !important;
            font-weight: 800 !important;
            border-bottom: 1px solid rgba(148, 163, 184, 0.22) !important;
        }

        section.main td,
        section.main .v8-table td {
            background: #0f172a !important;
            color: #f8fafc !important;
            font-weight: 600 !important;
            border-bottom: 1px solid rgba(148, 163, 184, 0.10) !important;
        }

        section.main .v8-table tbody tr:hover {
            background: #1e293b !important;
        }

        section.main [data-testid="stDataFrame"] {
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            border-radius: 12px !important;
        }

        section.main [data-testid="stDataFrame"] * {
            color: #f8fafc !important;
        }

        /* Buttons */
        section.main [data-testid="stButton"] button[kind="primary"],
        section.main [data-testid="stFormSubmitButton"] button[kind="primary"],
        section.main [data-testid="stFormSubmitButton"] button {
            background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
            color: #ffffff !important;
            border: 1px solid rgba(129, 140, 248, 0.4) !important;
            box-shadow: 0 4px 18px rgba(99, 102, 241, 0.3) !important;
        }

        section.main [data-testid="stButton"] button[kind="secondary"],
        section.main [data-testid="stButton"] button:not([kind="primary"]) {
            background: #1e293b !important;
            color: #f8fafc !important;
            border: 1.5px solid rgba(148, 163, 184, 0.28) !important;
        }

        /* Hero Banners in Main Area */
        section.main .v8-hero,
        section.main .hr-hero,
        section.main .command-hero {
            background: linear-gradient(135deg, #091633 0%, #102554 52%, #17336d 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        section.main .v8-hero *,
        section.main .hr-hero *,
        section.main .command-hero * {
            color: #ffffff !important;
        }

        section.main .v8-hero p,
        section.main .hr-hero-subtitle,
        section.main .v8-eyebrow,
        section.main .v8-date-label {
            color: #cbd5e1 !important;
        }

        /* Announcements Banner */
        section.main .ems-banner {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95)) !important;
            border: 1px solid rgba(129, 140, 248, 0.3) !important;
        }

        section.main .ems-banner strong,
        section.main .ems-banner-title {
            color: #ffffff !important;
            font-weight: 800 !important;
        }

        section.main .ems-banner div,
        section.main .ems-banner-content,
        section.main .ems-banner-author {
            color: #cbd5e1 !important;
        }
        """

    else:
        main_css = """
        /* ========================================================
           MAIN CONTENT AREA - LIGHT DASHBOARD (WHITE DASHBOARD)
           Deep black / dark navy text (#0f172a / #000000) on all white surfaces!
           ======================================================== */
        section.main,
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        .stApp:not([data-testid="stSidebar"]) {
            background:
                radial-gradient(circle at 85% 0%, rgba(37, 99, 235, 0.055), transparent 28%),
                linear-gradient(180deg, #f8faff 0%, #f5f7fb 48%, #f3f6fa 100%) !important;
            color: #0f172a !important;
        }

        /* Headings: Deep Black */
        section.main h1,
        section.main h2,
        section.main h3,
        section.main h4,
        section.main h5,
        section.main h6,
        section.main .page-title,
        section.main .section-heading,
        section.main .section-title,
        section.main .login-title,
        section.main .brand-title {
            color: #0f172a !important;
            font-weight: 850 !important;
        }

        /* Body & Elements in Main: Deep Dark */
        section.main p,
        section.main span,
        section.main div:not(.v8-hero):not(.hr-hero):not(.command-hero):not([style*="linear-gradient(135deg,#1e3a8a"]),
        section.main li,
        section.main strong,
        section.main b,
        section.main em,
        section.main label,
        section.main dt,
        section.main dd {
            color: #0f172a !important;
        }

        section.main .page-subtitle,
        section.main .section-subtitle,
        section.main .v8-eyebrow,
        section.main .page-eyebrow,
        section.main .brand-kicker,
        section.main .login-description,
        section.main .brand-description,
        section.main small,
        section.main caption,
        section.main [data-testid="stCaptionContainer"],
        section.main [data-testid="stCaptionContainer"] p,
        section.main .v8-kpi-note,
        section.main .metric-description,
        section.main .metric-note,
        section.main .v8-role-info span,
        section.main .v8-employee-cell span,
        section.main .muted,
        section.main .text-muted,
        section.main .advanced-panel-head p,
        section.main .identity-banner span,
        section.main .insight-card p,
        section.main .quality-score span,
        section.main .login-trust span,
        section.main .brand-footer,
        section.main .trust-label {
            color: #334155 !important;
            font-weight: 600 !important;
        }

        /* Markdown Container */
        section.main [data-testid="stMarkdownContainer"] * {
            color: #0f172a !important;
        }

        section.main [data-testid="stMarkdownContainer"] strong,
        section.main [data-testid="stMarkdownContainer"] b {
            color: #000000 !important;
            font-weight: 850 !important;
        }

        section.main [data-testid="stMarkdownContainer"] code {
            background: #f1f5f9 !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
            padding: 2px 6px !important;
            font-weight: 700 !important;
        }

        /* Form Labels in Main */
        section.main [data-testid="stWidgetLabel"] label,
        section.main [data-testid="stWidgetLabel"] p,
        section.main [data-testid="stWidgetLabel"] * {
            color: #0f172a !important;
            font-weight: 750 !important;
            font-size: 13.5px !important;
        }

        /* Inputs in Main */
        section.main [data-testid="stTextInput"] input,
        section.main [data-testid="stNumberInput"] input,
        section.main [data-testid="stDateInput"] input,
        section.main [data-testid="stTextArea"] textarea {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1.5px solid #cbd5e1 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }

        section.main input::placeholder,
        section.main textarea::placeholder {
            color: #64748b !important;
            opacity: 1 !important;
        }

        /* Selectboxes in Main */
        section.main [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1.5px solid #cbd5e1 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }

        section.main [data-testid="stSelectbox"] div[data-baseweb="select"] * {
            color: #0f172a !important;
        }

        div[data-baseweb="popover"],
        ul[role="listbox"],
        li[role="option"] {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
        }

        li[role="option"]:hover,
        li[role="option"][aria-selected="true"] {
            background: #eff6ff !important;
            color: #1d4ed8 !important;
        }

        /* Forms in Main */
        section.main [data-testid="stForm"],
        section.main div[data-testid="stForm"] {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04) !important;
        }

        /* Cards, Panels, Containers in Main */
        section.main .v8-panel,
        section.main .v8-kpi,
        section.main .v8-mini-card,
        section.main .v8-table-panel,
        section.main .metric-card,
        section.main .panel,
        section.main .kpi-card,
        section.main .panel-card,
        section.main .workspace-panel,
        section.main [data-testid="stVerticalBlockBorderWrapper"],
        section.main .advanced-panel,
        section.main .insight-card,
        section.main .ems-announcement-card,
        section.main .ems-stat-chip,
        section.main .profile-card,
        section.main .profile-item,
        section.main .emp-leave-card {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            color: #0f172a !important;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06) !important;
        }

        section.main .v8-kpi-value,
        section.main .kpi-value,
        section.main .metric-value,
        section.main .v8-mini-body strong,
        section.main .v8-data-row-top strong,
        section.main .v8-role-info strong,
        section.main .v8-employee-cell strong,
        section.main .ems-stat-chip strong,
        section.main .emp-leave-total,
        section.main .advanced-panel-head h3,
        section.main .identity-banner strong,
        section.main .advanced-data-grid strong,
        section.main .position-highlight strong,
        section.main .insight-card strong,
        section.main .quality-score strong,
        section.main .trust-value,
        section.main .brand-product,
        section.main [data-testid="stMetricValue"] * {
            color: #0f172a !important;
            font-weight: 850 !important;
        }

        section.main .v8-kpi-label,
        section.main .kpi-label,
        section.main .metric-label,
        section.main .v8-mini-body span,
        section.main .v8-data-row-top span,
        section.main .v8-role-info span,
        section.main .v8-employee-cell span,
        section.main .emp-leave-label,
        section.main .emp-leave-sub,
        section.main [data-testid="stMetricLabel"] * {
            color: #334155 !important;
            font-weight: 700 !important;
        }

        section.main .emp-leave-meta {
            color: #2563eb !important;
            font-weight: 700 !important;
        }

        section.main .identity-banner,
        section.main .position-highlight {
            background: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
        }

        /* Expanders in Main Area */
        section.main [data-testid="stExpander"] {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 14px !important;
        }

        section.main [data-testid="stExpander"] details summary {
            background: #f8fafc !important;
            color: #0f172a !important;
            font-weight: 750 !important;
            border-radius: 14px !important;
        }

        section.main [data-testid="stExpander"] details summary * {
            color: #0f172a !important;
            font-weight: 750 !important;
        }

        section.main [data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
            background: #ffffff !important;
            color: #0f172a !important;
        }

        /* Tabs in Main Area */
        section.main [data-testid="stTabs"] button {
            color: #475569 !important;
            font-weight: 650 !important;
            font-size: 14px !important;
        }

        section.main [data-testid="stTabs"] button[aria-selected="true"] {
            color: #2563eb !important;
            font-weight: 800 !important;
            border-bottom: 2.5px solid #2563eb !important;
        }

        /* Tables & DataFrames */
        section.main table {
            background: #ffffff !important;
            color: #0f172a !important;
        }

        section.main th,
        section.main .v8-table th {
            background: #f1f5f9 !important;
            color: #0f172a !important;
            font-weight: 800 !important;
            border-bottom: 2px solid #cbd5e1 !important;
        }

        section.main td,
        section.main .v8-table td {
            background: #ffffff !important;
            color: #0f172a !important;
            font-weight: 600 !important;
            border-bottom: 1px solid #e2e8f0 !important;
        }

        section.main .v8-table tbody tr:hover {
            background: #f8fafc !important;
        }

        section.main [data-testid="stDataFrame"] {
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px !important;
        }

        section.main [data-testid="stDataFrame"] * {
            color: #0f172a !important;
        }

        /* Buttons */
        section.main [data-testid="stButton"] button[kind="primary"],
        section.main [data-testid="stFormSubmitButton"] button[kind="primary"],
        section.main [data-testid="stFormSubmitButton"] button {
            background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
            color: #ffffff !important;
            border: 1px solid #1d4ed8 !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25) !important;
        }

        section.main [data-testid="stButton"] button[kind="secondary"],
        section.main [data-testid="stButton"] button:not([kind="primary"]) {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1.5px solid #cbd5e1 !important;
        }

        /* Hero Banners in Main Area: ALWAYS WHITE TEXT on Dark Navy Gradient */
        section.main .v8-hero,
        section.main .hr-hero,
        section.main .command-hero {
            background: linear-gradient(135deg, #091633 0%, #102554 52%, #17336d 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
        }

        section.main .v8-hero *,
        section.main .hr-hero *,
        section.main .command-hero * {
            color: #ffffff !important;
        }

        section.main .v8-hero p,
        section.main .hr-hero-subtitle,
        section.main .v8-eyebrow,
        section.main .v8-date-label {
            color: #cbd5e1 !important;
        }

        section.main .v8-hero h1 {
            color: #ffffff !important;
        }

        /* Announcements Banner in Light Mode */
        section.main .ems-banner {
            background: linear-gradient(135deg, #eff6ff, #f8fafc) !important;
            border: 1.5px solid #bfdbfe !important;
        }

        section.main .ems-banner strong,
        section.main .ems-banner-title {
            color: #0f172a !important;
            font-weight: 800 !important;
        }

        section.main .ems-banner div,
        section.main .ems-banner-content,
        section.main .ems-banner-author {
            color: #334155 !important;
        }

        section.main .v8-actions-panel + div button {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1.5px solid #cbd5e1 !important;
        }

        /* Net Salary Banner in Payslip */
        section.main div[style*="linear-gradient(135deg,#1e3a8a"] * {
            color: #ffffff !important;
        }
        """

    return f"{sidebar_css}\n{main_css}"


def apply_theme(theme: str = "dark") -> None:
    """Inject the unified theme styling into the current Streamlit app."""
    css = get_theme_css(theme)
    st.html(f"<style>{css}</style>")
