"""
Theme Manager — Light & Dark Mode for the Learning Disability Detection app.

Provides:
- A persistent theme preference in st.session_state
- A reusable sidebar toggle widget (`render_theme_toggle`)
- A single CSS injector (`apply_theme`) that paints the whole app, including
  Streamlit's chrome (sidebar, buttons, inputs, tabs, metrics) and our custom
  widget classes (.instruction-box, .game-card, .stars-banner, .progress-box,
  .encouragement, .target-display, .countdown-display, ...).

The dark theme keeps high contrast and dyslexia-friendly typography so it stays
accessible for children.
"""

from __future__ import annotations

import streamlit as st


THEME_KEY = "ui_theme"  # "light" or "dark"


def get_theme() -> str:
    """Return the current theme ("light" or "dark"). Defaults to light."""
    theme = st.session_state.get(THEME_KEY, "light")
    if theme not in ("light", "dark"):
        theme = "light"
        st.session_state[THEME_KEY] = theme
    return theme


def set_theme(theme: str) -> None:
    """Persist theme preference."""
    if theme not in ("light", "dark"):
        theme = "light"
    st.session_state[THEME_KEY] = theme


def toggle_theme() -> None:
    """Flip between light and dark."""
    set_theme("dark" if get_theme() == "light" else "light")


# ---------------------------------------------------------------------------
# Theme palettes
# ---------------------------------------------------------------------------

_LIGHT = {
    "bg":            "#F7FAFD",
    "bg_alt":        "#FFFFFF",
    "panel":         "#FFFFFF",
    "panel_alt":     "#F1F5F9",
    "text":          "#1A202C",
    "text_soft":     "#3D4856",
    "muted":         "#5B6776",
    "border":        "#D6DEE8",
    "border_strong": "#9AA8BA",
    "accent":        "#1565C0",
    "accent_alt":    "#7B1FA2",
    "success":       "#2E7D32",
    "warning":       "#E65100",
    "danger":        "#C62828",
    "shadow":        "0 4px 18px rgba(15, 30, 60, 0.08)",
    "input_bg":      "#FFFFFF",
    "input_text":    "#1A202C",
    "sidebar_bg":    "#E8F1FB",
    "sidebar_text":  "#1A202C",
    "card_bg":       "#FFFFFF",
}

_DARK = {
    "bg":            "#0E1422",
    "bg_alt":        "#141C2E",
    "panel":         "#1A2336",
    "panel_alt":     "#222C42",
    "text":          "#F2F5FA",
    "text_soft":     "#D6DEEC",
    "muted":         "#9AA8BA",
    "border":        "#2D3A55",
    "border_strong": "#42547A",
    "accent":        "#64B5F6",
    "accent_alt":    "#CE93D8",
    "success":       "#81C784",
    "warning":       "#FFB74D",
    "danger":        "#EF9A9A",
    "shadow":        "0 6px 22px rgba(0, 0, 0, 0.45)",
    "input_bg":      "#1A2336",
    "input_text":    "#F2F5FA",
    "sidebar_bg":    "#10182A",
    "sidebar_text":  "#F2F5FA",
    "card_bg":       "#1A2336",
}


def _palette(theme: str) -> dict:
    return _DARK if theme == "dark" else _LIGHT


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

def _build_css(theme: str) -> str:
    p = _palette(theme)
    is_dark = theme == "dark"

    # In dark mode we soften the bright pastel backgrounds used by per-page
    # widgets (e.g. instruction-box on white) so that text stays readable.
    instruction_bg = p["panel"]
    instruction_text = p["text"]
    instruction_border = p["accent"]

    # Make sure custom inline gradient cards stay legible: in dark mode we
    # overlay a slight darken filter and force text to light.
    inline_force = ""
    if is_dark:
        inline_force = """
        /* Force readable text inside inline-styled gradient cards in dark mode */
        div[style*="linear-gradient"] :is(h1, h2, h3, h4, p, strong, span) {
            color: #FFFFFF !important;
        }
        div[style*="background: #E3F2FD"],
        div[style*="background:#E3F2FD"],
        div[style*="background: #FFF3E0"],
        div[style*="background:#FFF3E0"],
        div[style*="background: #F3E5F5"],
        div[style*="background:#F3E5F5"],
        div[style*="background: #FFCDD2"],
        div[style*="background:#FFCDD2"],
        div[style*="background: #C8E6C9"],
        div[style*="background:#C8E6C9"],
        div[style*="background: #FFFFFF"],
        div[style*="background:#FFFFFF"],
        div[style*="background: #ECEFF1"],
        div[style*="background:#ECEFF1"] {
            background: %(panel)s !important;
            color: %(text)s !important;
            border-color: %(border)s !important;
        }
        div[style*="background: #E3F2FD"] *,
        div[style*="background:#E3F2FD"] *,
        div[style*="background: #FFF3E0"] *,
        div[style*="background:#FFF3E0"] *,
        div[style*="background: #F3E5F5"] *,
        div[style*="background:#F3E5F5"] *,
        div[style*="background: #FFCDD2"] *,
        div[style*="background:#FFCDD2"] *,
        div[style*="background: #C8E6C9"] *,
        div[style*="background:#C8E6C9"] *,
        div[style*="background: #FFFFFF"] *,
        div[style*="background:#FFFFFF"] *,
        div[style*="background: #ECEFF1"] *,
        div[style*="background:#ECEFF1"] * {
            color: %(text)s !important;
        }
        """ % {"panel": p["panel"], "text": p["text"], "border": p["border"]}

    return f"""
    <style id="app-theme">
    /* Dyslexia-friendly font, loaded once for the whole app */
    @import url('https://fonts.cdnfonts.com/css/opendyslexic');

    :root {{
        --app-font: 'OpenDyslexic', 'Comic Sans MS', 'Lexend', 'Arial Rounded MT Bold', 'Arial', sans-serif;
        --app-bg: {p['bg']};
        --app-bg-alt: {p['bg_alt']};
        --app-panel: {p['panel']};
        --app-panel-alt: {p['panel_alt']};
        --app-text: {p['text']};
        --app-text-soft: {p['text_soft']};
        --app-muted: {p['muted']};
        --app-border: {p['border']};
        --app-border-strong: {p['border_strong']};
        --app-accent: {p['accent']};
        --app-accent-alt: {p['accent_alt']};
        --app-success: {p['success']};
        --app-warning: {p['warning']};
        --app-danger: {p['danger']};
        --app-shadow: {p['shadow']};
        --app-input-bg: {p['input_bg']};
        --app-input-text: {p['input_text']};
        --app-sidebar-bg: {p['sidebar_bg']};
        --app-sidebar-text: {p['sidebar_text']};
        --app-card-bg: {p['card_bg']};
    }}

    /* ---- Global dyslexia-friendly typography ---- */
    html, body, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"],
    [data-testid="stHeader"],
    [data-testid="stMarkdownContainer"],
    [data-testid="stMetric"],
    [data-testid="stDataFrame"],
    [data-testid="stTable"],
    .block-container,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp p, .stApp li, .stApp span, .stApp label, .stApp small, .stApp strong, .stApp em,
    .stApp button, .stApp input, .stApp textarea, .stApp select, .stApp option,
    .stButton > button, .stDownloadButton > button,
    .stTextInput input, .stNumberInput input, .stTextArea textarea,
    .stSelectbox div, .stMultiSelect div, .stRadio label, .stCheckbox label,
    .stTabs [data-baseweb="tab"], .stTabs [data-baseweb="tab-list"],
    .stAlert, .stExpander,
    .child-header, .child-subheader, .fun-header, .child-title, .game-header,
    .instruction-box, .how-to-play, .level-text, .instruction-text,
    .game-card, .difficulty-card, .mode-card, .task-card, .section-card,
    .progress-card, .progress-box, .stars-banner, .stars-display, .stars-earned,
    .encouragement, .target-display, .countdown-display, .question-display,
    .trophy-box, .teacher-header,
    .aud-title, .wm-title, .wm-digit, .wm-pill, .ps-title, .ps-pill, .fa-title, .fa-pill,
    .game-title, .game-desc, .game-icon,
    .button-text {{
        font-family: var(--app-font) !important;
        letter-spacing: 0.04em;
    }}

    /* Slightly bigger letter spacing on body copy improves OpenDyslexic legibility */
    .stApp p, .stApp li, .instruction-box, .how-to-play, .game-desc {{
        letter-spacing: 0.06em;
    }}

    /* ---- Restore icon fonts (Material Symbols, etc.) -------------------
       The dyslexia-friendly font override above (.stApp span ...) was also
       hitting Streamlit's icon spans, which made the sidebar-collapse arrow
       and other icons render as raw text like "keyboard_double_arrow_right".
       The selectors below force the proper icon font back on those elements
       and undo the letter-spacing tweak so the glyphs still align. */
    .stApp .material-symbols-rounded,
    .stApp .material-symbols-outlined,
    .stApp .material-symbols-sharp,
    .stApp .material-icons,
    .stApp .material-icons-outlined,
    .stApp .material-icons-round,
    .stApp [data-testid="stIconMaterial"],
    .stApp [data-testid="stIcon"],
    .stApp [data-testid="stIconMaterial"] *,
    .stApp [data-testid="stIcon"] * {{
        font-family: 'Material Symbols Rounded',
                     'Material Symbols Outlined',
                     'Material Icons Rounded',
                     'Material Icons',
                     sans-serif !important;
        letter-spacing: 0 !important;
        font-feature-settings: 'liga' !important;
    }}

    /* ---- Base app ---- */
    .stApp, [data-testid="stAppViewContainer"] {{
        background: var(--app-bg) !important;
        color: var(--app-text) !important;
    }}
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}
    .block-container {{
        background: transparent !important;
        color: var(--app-text) !important;
    }}
    .stApp p, .stApp li, .stApp span, .stApp label,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
        color: var(--app-text);
    }}
    .stApp a {{ color: var(--app-accent); }}
    hr, [data-testid="stMarkdownContainer"] hr {{
        border-color: var(--app-border) !important;
    }}

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {{
        background: var(--app-sidebar-bg) !important;
    }}
    [data-testid="stSidebar"] * {{
        color: var(--app-sidebar-text) !important;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: var(--app-border) !important;
    }}

    /* ---- Buttons ---- */
    .stButton > button, .stDownloadButton > button {{
        background: var(--app-panel) !important;
        color: var(--app-text) !important;
        border: 2px solid var(--app-border-strong) !important;
        border-radius: 14px !important;
        font-weight: 600 !important;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{
        background: var(--app-panel-alt) !important;
        border-color: var(--app-accent) !important;
        color: var(--app-text) !important;
    }}
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {{
        background: linear-gradient(135deg, var(--app-accent), var(--app-accent-alt)) !important;
        border: none !important;
        color: #FFFFFF !important;
    }}

    /* ---- Inputs ---- */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {{
        background: var(--app-input-bg) !important;
        color: var(--app-input-text) !important;
        border: 2px solid var(--app-border) !important;
        border-radius: 10px !important;
    }}
    .stRadio label, .stCheckbox label {{
        color: var(--app-text) !important;
    }}

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] {{
        background: var(--app-panel) !important;
        border-radius: 12px;
        padding: 0.25rem;
        border: 1px solid var(--app-border);
    }}
    .stTabs [data-baseweb="tab"] {{
        color: var(--app-text-soft) !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: var(--app-accent) !important;
    }}

    /* ---- Metrics ---- */
    [data-testid="stMetric"] {{
        background: var(--app-panel) !important;
        border: 1px solid var(--app-border) !important;
        border-radius: 14px !important;
        padding: 1rem !important;
        box-shadow: var(--app-shadow);
    }}
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {{
        color: var(--app-text) !important;
    }}

    /* ---- Alerts (info / success / warning / error) keep their accent
            colors but adapt background in dark mode for readability ---- */
    [data-testid="stAlert"] {{
        border-radius: 14px !important;
    }}

    /* ---- Custom shared widgets used across pages ---- */
    .instruction-box, .how-to-play, .level-text {{
        background: {instruction_bg} !important;
        color: {instruction_text} !important;
        border: 3px solid {instruction_border} !important;
        border-radius: 15px;
        padding: 1.5rem;
        font-size: 1.3rem;
        line-height: 1.7;
        box-shadow: var(--app-shadow);
    }}
    .instruction-box *, .how-to-play *, .level-text * {{
        color: {instruction_text} !important;
    }}

    .stars-banner {{
        background: linear-gradient(135deg, #FFD54F 0%, #FFB300 100%) !important;
        color: #4A2E00 !important;
        border-radius: 18px;
        padding: 0.9rem 1.4rem;
        font-weight: 700;
        text-align: center;
        box-shadow: var(--app-shadow);
    }}
    .stars-banner * {{ color: #4A2E00 !important; }}

    .game-card, .difficulty-card, .mode-card, .task-card, .section-card,
    .progress-card, .progress-box, .mode-select-card {{
        background: var(--app-card-bg) !important;
        color: var(--app-text) !important;
        border: 2px solid var(--app-border) !important;
        border-radius: 18px;
        box-shadow: var(--app-shadow);
    }}
    .game-card *, .difficulty-card *, .mode-card *, .task-card *,
    .section-card *, .progress-card *, .progress-box *, .mode-select-card * {{
        color: var(--app-text) !important;
    }}

    .encouragement {{
        background: linear-gradient(135deg, #66BB6A 0%, #43A047 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 16px;
        padding: 1.1rem 1.4rem;
        text-align: center;
        font-weight: 700;
        box-shadow: var(--app-shadow);
    }}
    .encouragement * {{ color: #FFFFFF !important; }}

    .child-header, .fun-header, .child-title, .game-header {{
        color: var(--app-accent) !important;
        text-shadow: none !important;
    }}
    .child-subheader {{ color: var(--app-text-soft) !important; }}

    .target-display, .countdown-display, .question-display, .trophy-box,
    .stars-earned {{
        color: #FFFFFF !important;
        box-shadow: var(--app-shadow);
    }}

    .stars-display {{
        background: linear-gradient(135deg, #FFD54F 0%, #FFB300 100%) !important;
        color: #4A2E00 !important;
    }}
    .stars-display * {{ color: #4A2E00 !important; }}

    .teacher-header {{
        background: var(--app-panel-alt) !important;
        color: var(--app-text) !important;
        border: 1px solid var(--app-border) !important;
        border-radius: 14px;
    }}
    .teacher-header * {{ color: var(--app-text) !important; }}

    /* DataFrames */
    [data-testid="stDataFrame"] {{
        background: var(--app-panel) !important;
        border-radius: 12px;
        padding: 4px;
    }}

    /* Theme toggle pill */
    .theme-toggle-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: var(--app-panel-alt);
        color: var(--app-text);
        border: 1px solid var(--app-border);
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        font-size: 0.95rem;
        font-weight: 600;
    }}

    {inline_force}
    </style>
    """


def apply_theme() -> None:
    """Inject CSS for the current theme. Call once per page after st.set_page_config."""
    theme = get_theme()
    st.markdown(_build_css(theme), unsafe_allow_html=True)


def render_theme_toggle(location: str = "sidebar", key_suffix: str = "") -> None:
    """
    Render a small Light/Dark toggle.

    Parameters
    ----------
    location : "sidebar" | "main"
        Where to draw the toggle.
    key_suffix : str
        Distinguishes multiple toggles on the same page (Streamlit needs unique keys).
    """
    container = st.sidebar if location == "sidebar" else st
    current = get_theme()
    icon = "🌙" if current == "light" else "☀️"
    label = "Dark mode" if current == "light" else "Light mode"

    container.markdown(
        f'<div class="theme-toggle-pill">{icon} <span>Theme: '
        f'{"Light" if current == "light" else "Dark"}</span></div>',
        unsafe_allow_html=True,
    )
    if container.button(
        f"{icon} Switch to {label}",
        key=f"theme_toggle_btn_{key_suffix or location}",
        use_container_width=True,
    ):
        toggle_theme()
        st.rerun()
