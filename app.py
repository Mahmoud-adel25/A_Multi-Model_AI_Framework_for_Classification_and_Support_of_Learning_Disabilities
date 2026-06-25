"""
Learning Disability Detection & Support System
Child-Friendly, Accessible Design with Teacher/Parent Monitoring

Tabs: Home | Child Registration/Selection | Classification | Support Layer | Parent/Teacher Dashboard
"""

import streamlit as st
import sys
import os
import uuid
import random
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.session_manager import SessionManager
from utils.logger import get_logger, log_child_login
from utils.theme import apply_theme, render_theme_toggle
from database.db_handler import DatabaseHandler

logger = get_logger("app")


# Pattern that matches the auto-generated "Friend-XXXX" placeholder names.
# Used in the teacher dashboard to highlight anonymous accounts that still
# need a real child name.
ANONYMOUS_NAME_RE = re.compile(r"^Friend[-_]\d{3,6}$", re.IGNORECASE)
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "Teacher@123"

EXERCISE_CHARTS = {
    "attention": {
        "name": "Attention & Focus",
        "metric": "Focus Score (%)",
        "color": "#2E86DE",
        "normalize": lambda row: row.get("score"),
    },
    "visual_memory": {
        "name": "Visual Memory",
        "metric": "Memory Score",
        "color": "#8E44AD",
        "normalize": lambda row: (row.get("accuracy") or 0) * 100 if row.get("accuracy") is not None else None,
    },
    "auditory_memory": {
        "name": "Auditory Memory",
        "metric": "Rounds Remembered",
        "color": "#16A085",
        "normalize": lambda row: (row.get("accuracy") or 0) * 100 if row.get("accuracy") is not None else None,
    },
    "working_memory": {
        "name": "Working Memory",
        "metric": "Max Sequence Length",
        "color": "#E67E22",
        "normalize": lambda row: (row.get("accuracy") or 0) * 100 if row.get("accuracy") is not None else None,
    },
    "processing_speed": {
        "name": "Processing Speed",
        "metric": "Speed Score (%)",
        "color": "#C0392B",
        "normalize": lambda row: row.get("score"),
    },
    "final_assessment": {
        "name": "Final Assessment",
        "metric": "Total Score",
        "color": "#34495E",
        "normalize": lambda row: row.get("score"),
    },
}


def _generate_anon_name(existing_names: list[str]) -> str:
    """Pick an unused ``Friend-XXXX`` placeholder name. The 4-digit suffix
    keeps the temporary identifier short, easy to read aloud, and easy for
    the teacher to spot in the children list."""
    taken = {n.lower() for n in existing_names if n}
    for _ in range(50):
        candidate = f"Friend-{random.randint(1000, 9999)}"
        if candidate.lower() not in taken:
            return candidate
    # Extremely unlikely fallback — widen the suffix to avoid a collision.
    return f"Friend-{random.randint(10000, 999999)}"


def get_admin_credentials():
    """Read Teacher/Parent admin credentials from Streamlit secrets, with demo defaults."""
    try:
        username = st.secrets.get("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
        password = st.secrets.get("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    except Exception:
        username = DEFAULT_ADMIN_USERNAME
        password = DEFAULT_ADMIN_PASSWORD

    return str(username), str(password)


def show_teacher_login():
    """Require admin login before opening Teacher/Parent mode."""
    with st.sidebar:
        st.markdown("### 🎨 Appearance")
        render_theme_toggle(location="sidebar", key_suffix="teacher_login")
        st.divider()
        if st.button("🔙 Back to Mode Selection", use_container_width=True):
            st.session_state.app_mode = "child"
            st.session_state.mode_selected = False
            st.session_state.teacher_authenticated = False
            st.rerun()

    st.markdown('<div class="teacher-header"><h2>🔐 Teacher/Parent Login</h2></div>',
                unsafe_allow_html=True)
    st.info("Enter the admin credentials to view child progress and assessment details.")

    expected_username, expected_password = get_admin_credentials()

    with st.form("teacher_login_form"):
        username = st.text_input("Username", placeholder=" ")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        from utils.auth import verify_teacher_credentials

        if verify_teacher_credentials(username, password, expected_username, expected_password):
            st.session_state.teacher_authenticated = True
            st.success("Login successful. Opening Teacher/Parent dashboard...")
            st.rerun()
        else:
            st.error("Incorrect username or password. Please try again.")

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Learning Fun! - Practice & Play",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session
SessionManager.initialize_session()

# ============================================================
# ACCESSIBILITY CSS - Dyslexia-friendly, high contrast, large text
# ============================================================
def load_accessibility_css():
    st.markdown("""
    <style>
    /* Import OpenDyslexic font for accessibility */
    @import url('https://fonts.cdnfonts.com/css/opendyslexic');
    
    /* Dyslexia-friendly defaults */
    .stApp {
        font-family: 'OpenDyslexic', 'Comic Sans MS', 'Arial', sans-serif;
        line-height: 1.8;
        letter-spacing: 0.12em;
    }
    
    /* Instructional text: black, high contrast, large - child readable */
    .instruction-text, .how-to-play, .level-text {
        color: #000000 !important;
        font-size: 1.35rem !important;
        line-height: 1.8 !important;
        font-weight: 500;
    }
    
    .child-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1565C0;
        text-align: center;
        padding: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .child-subheader {
        font-size: 1.5rem;
        color: #000000;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Large, colorful buttons for children */
    .big-button {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        min-height: 200px;
        text-decoration: none;
    }
    
    .big-button:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }
    
    .button-blue {
        background: linear-gradient(135deg, #42A5F5 0%, #1E88E5 100%);
        color: white;
    }
    
    .button-green {
        background: linear-gradient(135deg, #66BB6A 0%, #43A047 100%);
        color: white;
    }
    
    .button-purple {
        background: linear-gradient(135deg, #AB47BC 0%, #8E24AA 100%);
        color: white;
    }
    
    .button-orange {
        background: linear-gradient(135deg, #FFA726 0%, #FB8C00 100%);
        color: white;
    }
    
    .button-icon {
        font-size: 4rem;
        margin-bottom: 0.5rem;
    }
    
    .button-text {
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
    }
    
    /* Star display */
    .stars-display {
        background: linear-gradient(135deg, #FFD54F 0%, #FFC107 100%);
        padding: 1rem 2rem;
        border-radius: 15px;
        text-align: center;
        font-size: 1.5rem;
        color: #5D4037;
        box-shadow: 0 4px 15px rgba(255,193,7,0.3);
    }
    
    .star-icon {
        font-size: 2rem;
        color: #FF6F00;
    }
    
    /* Progress indicator */
    .progress-card {
        background: #E3F2FD;
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        border: 3px solid #42A5F5;
    }
    
    /* Positive reinforcement messages */
    .encouragement {
        background: linear-gradient(135deg, #C8E6C9 0%, #A5D6A7 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        font-size: 1.8rem;
        color: #2E7D32;
        margin: 1rem 0;
        border: 3px solid #66BB6A;
    }
    
    /* Teacher mode styles */
    .teacher-header {
        background: #37474F;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    /* Hide default Streamlit elements for cleaner child UI */
    .child-mode footer {visibility: hidden;}
    .child-mode #MainMenu {visibility: hidden;}
    
    /* Large clickable areas */
    .stButton > button {
        font-size: 1.2rem;
        padding: 0.8rem 2rem;
        border-radius: 15px;
        font-family: 'OpenDyslexic', 'Comic Sans MS', sans-serif;
    }
    
    /* Input fields - larger and clearer */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        font-size: 1.2rem;
        padding: 0.8rem;
        border-radius: 10px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: #E3F2FD;
    }
    
    /* Remove clutter */
    .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }

    /* Mode-select cards (Child / Teacher landing page).
       Background and text colour come from the theme so both light & dark
       modes look correct; only structural styling lives here. */
    .mode-select-card {
        padding: 2rem 1rem 1.4rem 1rem;
        border-radius: 18px;
        text-align: center;
        margin-bottom: 0.6rem;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 3px solid #1565C0;
    }
    .mode-select-card.teacher { border-color: #7B1FA2; }
    .mode-select-card .mode-icon {
        font-size: 4.5rem;
        line-height: 1;
    }
    .mode-select-card .mode-title {
        font-size: 1.7rem;
        font-weight: 800;
        margin-top: 0.5rem;
    }
    .mode-select-card .mode-subtitle {
        font-size: 1.15rem;
        margin-top: 0.3rem;
        opacity: 0.85;
    }
    </style>
    """, unsafe_allow_html=True)


def show_mode_selector():
    """Show mode selection screen."""
    with st.sidebar:
        st.markdown("### 🎨 Appearance")
        render_theme_toggle(location="sidebar", key_suffix="mode_select")

    st.markdown('<p class="child-header">Welcome! 👋</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Who's using this today?")

        col_child, col_teacher = st.columns(2)

        with col_child:
            st.markdown(
                """
                <div class="mode-select-card">
                    <div class="mode-icon">🧒</div>
                    <div class="mode-title">I'm a Child</div>
                    <div class="mode-subtitle">Let's Play!</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Choose Child mode",
                         use_container_width=True,
                         key="child_mode_btn",
                         type="primary",
                         help="Fun learning activities!"):
                st.session_state.app_mode = "child"
                st.session_state.mode_selected = True
                st.rerun()

        with col_teacher:
            st.markdown(
                """
                <div class="mode-select-card teacher">
                    <div class="mode-icon">👨‍🏫</div>
                    <div class="mode-title">Teacher / Parent</div>
                    <div class="mode-subtitle">View Progress</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Choose Teacher mode",
                         use_container_width=True,
                         key="teacher_mode_btn",
                         type="primary",
                         help="See how your child is doing"):
                st.session_state.app_mode = "teacher"
                st.session_state.mode_selected = True
                st.session_state.teacher_authenticated = False
                st.rerun()


def show_child_home():
    """Child-friendly home: child registration/selection then main nav."""
    db = DatabaseHandler()
    user_id = SessionManager.get_user_id()
    parent_id = st.session_state.get("parent_id", "default")

    # ---- Child Registration / Selection (same child can login again) ----
    with st.sidebar:
        st.markdown("### 👤 Who is playing?")
        children = db.get_children_for_parent(parent_id)
        child_ids = [c["user_id"] for c in children]
        # If current session user was deleted (or no children), clear selection so we don't show stale stars
        if not child_ids or user_id not in child_ids:
            SessionManager.set_user_name(None)
            SessionManager.set_user_age(None)
            if not child_ids:
                SessionManager.set_user_id(str(uuid.uuid4())[:12])
            else:
                SessionManager.set_user_id(child_ids[0])  # pick first child so dropdown works
            user_id = SessionManager.get_user_id()

        child_options = [(c["user_id"], c.get("name") or f"Child {c['user_id'][:6]}") for c in children]
        choice_labels = [f"{name} (ID: {uid[:8]})" for uid, name in child_options]

        if child_options:
            selected_idx = st.selectbox(
                "Select yourself (or I'm new)",
                range(len(child_options) + 1),
                format_func=lambda i: choice_labels[i] if i < len(child_options) else "➕ I'm new!",
                key="child_select",
            )
            if selected_idx < len(child_options):
                chosen_id, chosen_name = child_options[selected_idx]
                SessionManager.set_user_id(chosen_id)
                SessionManager.set_user_name(chosen_name)
                SessionManager.set_user_age(db.get_user(chosen_id).get("age") or 8)
                db.create_or_get_user(chosen_id, name=chosen_name, age=SessionManager.get_user_age())
                log_child_login(logger, chosen_id, chosen_name, "login")
            else:
                # I'm new
                new_name = st.text_input("My name (new)", placeholder="Type your name", key="new_child_name")
                new_age = st.number_input("My age", min_value=4, max_value=18, value=8, key="new_child_age")
                if st.button("Create my account", key="create_child_btn") and new_name and new_name.strip():
                    existing = db.get_user_by_name(new_name.strip(), parent_id)
                    if existing:
                        st.info("That name already exists. Select yourself from the list above.")
                    else:
                        new_id = str(uuid.uuid4())[:12]
                        db.create_or_get_user(new_id, name=new_name.strip(), age=new_age, parent_id=parent_id)
                        SessionManager.set_user_id(new_id)
                        SessionManager.set_user_name(new_name.strip())
                        SessionManager.set_user_age(new_age)
                        log_child_login(logger, new_id, new_name.strip(), "register")
                        st.success("Welcome! You're all set.")
                        st.rerun()
                # Anonymous fallback — child can play without typing a name;
                # teacher can rename later from the dashboard.
                st.caption("No name yet? You can still play.")
                if st.button("🎮 Skip — just play!", key="skip_child_btn",
                             use_container_width=True):
                    anon_name = _generate_anon_name(
                        [c.get("name") or "" for c in children]
                    )
                    new_id = str(uuid.uuid4())[:12]
                    db.create_or_get_user(new_id, name=anon_name,
                                          age=int(new_age) if new_age else 8,
                                          parent_id=parent_id)
                    SessionManager.set_user_id(new_id)
                    SessionManager.set_user_name(anon_name)
                    SessionManager.set_user_age(int(new_age) if new_age else 8)
                    log_child_login(logger, new_id, anon_name, "register-anon")
                    st.success(f"Welcome, {anon_name}! Your teacher can give you a real name later.")
                    st.rerun()
        else:
            new_name = st.text_input("My name", placeholder="Type your name", key="new_child_name")
            new_age = st.number_input("My age", min_value=4, max_value=18, value=8, key="new_child_age")
            if st.button("Start!", key="create_first_btn") and new_name and new_name.strip():
                new_id = str(uuid.uuid4())[:12]
                db.create_or_get_user(new_id, name=new_name.strip(), age=new_age, parent_id=parent_id)
                SessionManager.set_user_id(new_id)
                SessionManager.set_user_name(new_name.strip())
                SessionManager.set_user_age(new_age)
                log_child_login(logger, new_id, new_name.strip(), "register")
                st.rerun()
            # Same anonymous shortcut for the very-first-child branch.
            st.caption("No name yet? You can still play.")
            if st.button("🎮 Skip — just play!", key="skip_first_btn",
                         use_container_width=True):
                anon_name = _generate_anon_name([])
                new_id = str(uuid.uuid4())[:12]
                db.create_or_get_user(new_id, name=anon_name,
                                      age=int(new_age) if new_age else 8,
                                      parent_id=parent_id)
                SessionManager.set_user_id(new_id)
                SessionManager.set_user_name(anon_name)
                SessionManager.set_user_age(int(new_age) if new_age else 8)
                log_child_login(logger, new_id, anon_name, "register-anon")
                st.rerun()

        user_id = SessionManager.get_user_id()
        # Only show stars for a child that still exists (not deleted)
        total_stars = db.get_total_stars(user_id) if user_id in child_ids else 0
        st.markdown(f"### ⭐ My Stars: {total_stars}")
        st.divider()
        child_name = SessionManager.get_user_name()
        child_age = SessionManager.get_user_age() or 8
        if child_name:
            st.markdown(f"**Name:** {child_name}")
        st.markdown(f"**Age:** {child_age}")
        if user_id in child_ids:
            db.create_or_get_user(user_id, name=child_name, age=child_age, parent_id=parent_id)
        st.divider()
        st.markdown("### 🎨 Appearance")
        render_theme_toggle(location="sidebar", key_suffix="child_home")
        st.divider()
        if st.button("🔙 Change Mode", use_container_width=True):
            st.session_state.mode_selected = False
            st.rerun()

    user_id = SessionManager.get_user_id()
    children_list = db.get_children_for_parent(parent_id)
    child_ids_list = [c["user_id"] for c in children_list]
    total_stars = db.get_total_stars(user_id) if user_id in child_ids_list else 0

    # Header with stars
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="child-header">🌟 Learning is Fun! 🌟</p>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stars-display">
            <span class="star-icon">⭐</span> 
            You have <strong>{total_stars}</strong> stars! 
            <span class="star-icon">⭐</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ---- Tools (writing check + big assessment) ----
    st.markdown("### 🛠️ My tools")
    tool_col1, tool_col2 = st.columns(2)

    with tool_col1:
        st.markdown("""
        <div class="big-button button-blue">
            <span class="button-icon">📝</span>
            <span class="button-text">Check My Writing</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📝 Check My Writing", use_container_width=True, key="btn_upload"):
            st.switch_page("pages/1_Upload_Handwriting.py")

    with tool_col2:
        st.markdown("""
        <div class="big-button button-orange">
            <span class="button-icon">🏆</span>
            <span class="button-text">Final Challenge</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🏆 Final Challenge", use_container_width=True, key="btn_final"):
            st.switch_page("pages/9_Final_Assessment.py")

    # ---- All exercises in one place ----
    st.markdown("### 🎮 My games")

    games_row1 = st.columns(3)
    with games_row1[0]:
        st.markdown("""
        <div class="big-button button-purple">
            <span class="button-icon">🎯</span>
            <span class="button-text">Focus Game</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎯 Focus Game", use_container_width=True, key="btn_attention"):
            st.switch_page("pages/4_Attention_Focus.py")

    with games_row1[1]:
        st.markdown("""
        <div class="big-button button-orange">
            <span class="button-icon">🧩</span>
            <span class="button-text">Memory Game</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🧩 Memory Game", use_container_width=True, key="btn_memory"):
            st.switch_page("pages/5_Visual_Memory.py")

    with games_row1[2]:
        st.markdown("""
        <div class="big-button button-green">
            <span class="button-icon">🔊</span>
            <span class="button-text">Sound Memory</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔊 Sound Memory", use_container_width=True, key="btn_auditory"):
            st.switch_page("pages/6_Auditory_Memory.py")

    games_row2 = st.columns(3)
    with games_row2[0]:
        st.markdown("""
        <div class="big-button button-blue">
            <span class="button-icon">🔢</span>
            <span class="button-text">Number Memory</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔢 Number Memory", use_container_width=True, key="btn_working"):
            st.switch_page("pages/7_Working_Memory.py")

    with games_row2[1]:
        st.markdown("""
        <div class="big-button button-purple">
            <span class="button-icon">⚡</span>
            <span class="button-text">Quick Think</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚡ Quick Think", use_container_width=True, key="btn_processing"):
            st.switch_page("pages/8_Processing_Speed.py")

    with games_row2[2]:
        st.markdown("""
        <div class="big-button button-green">
            <span class="button-icon">🎮</span>
            <span class="button-text">Practice Hub</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎮 Practice Hub", use_container_width=True, key="btn_practice"):
            st.switch_page("pages/3_Learning_Support.py")
    
    # Encouragement message
    st.markdown("<br>", unsafe_allow_html=True)
    
    encouragements = [
        "You're doing great! Keep it up! 🌟",
        "Every practice makes you better! 💪",
        "You're a star learner! ⭐",
        "Let's have fun learning today! 🎉",
        "You can do it! 🚀"
    ]
    import random
    st.markdown(f"""
    <div class="encouragement">
        {random.choice(encouragements)}
    </div>
    """, unsafe_allow_html=True)


def _format_chart_time(value):
    """Format database timestamps for chart labels."""
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(str(value)).strftime("%b %d, %Y")
    except ValueError:
        return str(value)[:16]


def _load_child_activity_histories(db, user_id):
    return {
        key: db.get_scores_by_child_and_activity(user_id, key, limit=100)
        for key in EXERCISE_CHARTS
    }


def _history_to_chart_frame(history, config):
    import pandas as pd

    df = pd.DataFrame(history)
    if df.empty:
        return df
    df["Date"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values("Date").reset_index(drop=True)
    df["Session"] = range(1, len(df) + 1)
    df["Score"] = pd.to_numeric(df["score"], errors="coerce")
    df["Normalized"] = df.apply(config["normalize"], axis=1)
    df["Normalized"] = pd.to_numeric(df["Normalized"], errors="coerce").clip(lower=0, upper=100)
    if len(df) >= 3:
        df["Moving Average"] = df["Score"].rolling(window=3, min_periods=1).mean()
    return df


def _style_plotly_figure(fig, title, subtitle=None):
    fig.update_layout(
        title={"text": f"{title}<br><sup>{subtitle or ''}</sup>", "x": 0.02, "xanchor": "left"},
        font={"family": "Arial, sans-serif", "size": 14, "color": "#263238"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 20, "r": 20, "t": 72, "b": 35},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(38,50,56,0.12)")
    return fig


def _render_overall_progress_chart(child_name, histories):
    import pandas as pd
    import plotly.graph_objects as go

    rows = []
    for key, config in EXERCISE_CHARTS.items():
        df = _history_to_chart_frame(histories.get(key, []), config)
        latest = df.dropna(subset=["Date"]).tail(1) if not df.empty else df
        if not latest.empty:
            row = latest.iloc[0]
            progress_value = row.get("Normalized")
            rows.append({
                "Exercise": config["name"],
                "Progress": progress_value if pd.notna(progress_value) else 0,
                "Label": f"{progress_value:.0f}%" if pd.notna(progress_value) else "—",
                "Last updated": _format_chart_time(row.get("timestamp")),
                "Color": config["color"] if pd.notna(progress_value) else "#B0B7C3",
            })
        else:
            rows.append({
                "Exercise": config["name"],
                "Progress": 0,
                "Label": "—",
                "Last updated": "—",
                "Color": "#B0B7C3",
            })

    df = pd.DataFrame(rows)
    fig = go.Figure()
    fig.add_bar(
        x=df["Exercise"],
        y=df["Progress"],
        text=df["Label"],
        textposition="outside",
        marker_color=df["Color"],
        hovertemplate="<b>%{x}</b><br>Progress: %{text}<br>Last updated: %{customdata}<extra></extra>",
        customdata=df["Last updated"],
    )
    fig.update_yaxes(range=[0, 105], title="Progress scale (0-100%)")
    fig.update_xaxes(title=None)
    _style_plotly_figure(fig, f"Overall Progress — {child_name}", "Latest available score for each activity")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        df[["Exercise", "Label", "Last updated"]].rename(columns={"Label": "Latest score"}),
        use_container_width=True,
        hide_index=True,
    )


def _render_exercise_chart(activity_key, history):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    config = EXERCISE_CHARTS[activity_key]
    if not history:
        st.info("No sessions recorded yet for this activity.")
        return

    df = _history_to_chart_frame(history, config)
    if df.empty or df["Score"].dropna().empty:
        st.info("No sessions recorded yet for this activity.")
        return

    attempts = len(df)
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Progress over time", "Session scores"),
        horizontal_spacing=0.12,
    )
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Score"],
            mode="lines+markers",
            name=config["metric"],
            line={"color": config["color"], "width": 3},
            marker={"size": 8},
            hovertemplate="%{x|%b %d, %Y}<br>Score: %{y:.1f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    if "Moving Average" in df:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Moving Average"],
                mode="lines",
                name="3-session trend",
                line={"color": "#5D6D7E", "width": 2, "dash": "dash"},
                hovertemplate="%{x|%b %d, %Y}<br>Trend: %{y:.1f}<extra></extra>",
            ),
            row=1,
            col=1,
        )
    if activity_key == "visual_memory" and "difficulty" in df:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Score"],
                mode="text",
                name="Difficulty",
                text=df["difficulty"].fillna(""),
                textposition="top center",
                textfont={"color": "#5D6D7E", "size": 12},
                hoverinfo="skip",
            ),
            row=1,
            col=1,
        )
    fig.add_trace(
        go.Bar(
            x=[f"Session {n}" for n in df["Session"]],
            y=df["Score"],
            name="Session score",
            marker_color=config["color"],
            hovertemplate="%{x}<br>Score: %{y:.1f}<extra></extra>",
        ),
        row=1,
        col=2,
    )
    fig.update_yaxes(title_text=config["metric"], row=1, col=1)
    fig.update_yaxes(title_text=config["metric"], row=1, col=2)
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Session", row=1, col=2)
    _style_plotly_figure(
        fig,
        f"{config['name']} — Score Over Time",
        f"{attempts} attempt{'s' if attempts != 1 else ''} recorded",
    )
    st.plotly_chart(fig, use_container_width=True)


def show_teacher_home():
    """Teacher/Parent dashboard: show child name, age, last activity; select from list."""
    st.markdown('<div class="teacher-header"><h2>👨‍🏫 Teacher/Parent Dashboard</h2></div>', 
                unsafe_allow_html=True)
    
    db = DatabaseHandler()
    parent_id = st.session_state.get("parent_id", "default")
    children = db.get_children_for_parent(parent_id)

    with st.sidebar:
        st.markdown("### Select Child")
        if not children:
            st.info("No children yet. Use Child Mode to add one.")
            user_id = None
        else:
            def _label(child):
                nm = child.get("name") or "Unnamed"
                # Mark Friend-XXXX placeholder names so the teacher can spot
                # accounts that still need a real name.
                tag = " 🆕 (no name)" if nm and ANONYMOUS_NAME_RE.match(nm) else ""
                return f"{nm}{tag} (ID: {child['user_id'][:8]})"
            options = [_label(c) for c in children]
            idx = st.selectbox("Child", range(len(children)), format_func=lambda i: options[i], key="teacher_child_select")
            user_id = children[idx]["user_id"] if idx is not None else (children[0]["user_id"] if children else None)
        st.divider()
        st.markdown("### 🎨 Appearance")
        render_theme_toggle(location="sidebar", key_suffix="teacher_home")
        st.divider()
        if st.button("🔙 Switch to Child Mode", use_container_width=True):
            st.session_state.app_mode = "child"
            st.session_state.teacher_authenticated = False
            st.session_state.pop("confirm_delete_child_id", None)
            st.rerun()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.teacher_authenticated = False
            st.session_state.mode_selected = False
            st.session_state.pop("confirm_delete_child_id", None)
            st.rerun()
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    if user_id is None:
        st.info("Add a child in Child Mode first, then return here to view progress.")
        return

    child_info = db.get_user(user_id)
    child_name = child_info.get("name") or "this child"
    progress = db.get_user_progress_summary(user_id)
    total_stars = db.get_total_stars(user_id)

    # Child name, ID, age, last activity
    st.markdown("### Child profile")
    col1, col2, col3, col4 = st.columns(4)
    current_name = child_info.get("name") or "—"
    is_anonymous = bool(current_name and ANONYMOUS_NAME_RE.match(current_name))
    with col1:
        st.metric(
            "Name",
            current_name,
            delta="placeholder" if is_anonymous else None,
            delta_color="off",
        )
    with col2:
        st.metric("Child ID", user_id[:12] + "…" if len(user_id) > 12 else user_id)
    with col3:
        age_val = child_info.get("age")
        st.metric("Age", str(age_val) if age_val is not None else "—")
    with col4:
        last_active = child_info.get("last_active")
        st.metric("Last activity", last_active[:16] if last_active else "—")

    # ---- Edit name (rename anonymous Friend-XXXX accounts) -----------------
    with st.expander(
        "✏️ Edit child name" + (" — placeholder detected" if is_anonymous else ""),
        expanded=is_anonymous,
    ):
        if is_anonymous:
            st.caption(
                f"This child started without a name and was given the placeholder "
                f"**{current_name}**. Type their real name below to update all "
                f"records linked to this child."
            )
        new_name_input = st.text_input(
            "Child name",
            value="" if is_anonymous else (child_info.get("name") or ""),
            placeholder="e.g. Sara",
            key=f"rename_input_{user_id}",
        )
        col_save, col_cancel = st.columns([1, 1])
        with col_save:
            if st.button("💾 Save name", key=f"rename_save_{user_id}",
                         type="primary", use_container_width=True):
                trimmed = (new_name_input or "").strip()
                if not trimmed:
                    st.warning("Please type a name first.")
                elif trimmed.lower() == (current_name or "").lower():
                    st.info("That's already the saved name.")
                else:
                    existing = db.get_user_by_name(trimmed, parent_id)
                    if existing and existing["user_id"] != user_id:
                        st.error(
                            f"Another child is already called “{trimmed}”. "
                            f"Pick a different name."
                        )
                    elif db.update_user_name(user_id, trimmed):
                        st.success(f"Renamed to **{trimmed}**.")
                        st.rerun()
                    else:
                        st.error("Could not save the new name. Try again.")
        with col_cancel:
            st.caption(" ")

    # Remove child (teachers/parents only) — with confirmation
    confirm_id = st.session_state.get("confirm_delete_child_id")
    if confirm_id == user_id:
        st.markdown("---")
        st.warning(f"**Are you sure?** This will permanently delete **{child_name}** and all their data (stars, writing checks, focus & memory sessions). This cannot be undone.")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, delete this child", type="primary", key="confirm_delete_yes"):
                db.delete_user(user_id)
                st.session_state.pop("confirm_delete_child_id", None)
                st.success(f"{child_name} has been removed.")
                st.rerun()
        with col_no:
            if st.button("Cancel", key="confirm_delete_no"):
                st.session_state.pop("confirm_delete_child_id", None)
                st.rerun()
    else:
        st.markdown("---")
        if st.button("🗑️ Remove this child from the system", type="secondary", key="remove_child_btn"):
            st.session_state["confirm_delete_child_id"] = user_id
            st.rerun()

    st.divider()

    # Overview cards
    attention_data = progress.get('modules', {}).get('attention', {})
    memory_data = progress.get('modules', {}).get('visual_memory', {})
    audio_data = progress.get('modules', {}).get('auditory_memory', {})
    wm_data = progress.get('modules', {}).get('working_memory', {})
    ps_data = progress.get('modules', {}).get('processing_speed', {})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Stars Earned", f"⭐ {total_stars}")
    with col2:
        classifications = progress.get('total_classifications', 0)
        st.metric("Writing Samples", classifications)
    with col3:
        st.metric("Focus Sessions", attention_data.get('total_sessions', 0))
    with col4:
        st.metric("Visual Memory", memory_data.get('total_sessions', 0))

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Auditory Memory", audio_data.get('total_sessions', 0))
    with col6:
        st.metric("Working Memory", wm_data.get('total_sessions', 0))
    with col7:
        st.metric("Processing Speed", ps_data.get('total_sessions', 0))
    with col8:
        fa_count = len(db.get_final_assessment_history(user_id, limit=999))
        st.metric("Final Assessments", fa_count)
    
    st.divider()

    try:
        activity_histories = _load_child_activity_histories(db, user_id)
    except Exception:
        st.warning("Could not load chart data. Please refresh the page.")
        activity_histories = {key: [] for key in EXERCISE_CHARTS}

    if not any(activity_histories.values()):
        st.info(f"🌱 {child_name} hasn't completed any activities yet. Encourage them to try their first exercise!")

    # Make the dashboard tab bar horizontally scrollable so every tab remains
    # accessible on narrow screens / when zoomed in. Only injected here
    # because show_teacher_home() runs on the dashboard route only —
    # the per-exercise pages execute their own scripts and aren't affected.
    st.markdown(
        """
        <style>
          .stTabs [data-baseweb="tab-list"] {
              flex-wrap: nowrap !important;
              overflow-x: auto !important;
              overflow-y: hidden !important;
              scrollbar-width: thin;
              scrollbar-color: var(--app-accent) transparent;
              -webkit-overflow-scrolling: touch;
          }
          .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
              height: 8px;
          }
          .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {
              background: var(--app-accent);
              border-radius: 999px;
          }
          .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-track {
              background: transparent;
          }
          .stTabs [data-baseweb="tab"] {
              flex: 0 0 auto !important;
              white-space: nowrap !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Overview",
        "🎯 Attention & Focus",
        "👁 Visual Memory",
        "👂 Auditory Memory",
        "🧠 Working Memory",
        "⚡ Processing Speed",
        "📝 Final Assessment",
    ])
    
    with tab1:
        st.subheader("Overview")
        _render_overall_progress_chart(child_name, activity_histories)
        st.divider()
        st.subheader("Activity Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Attention & Focus Module")
            if attention_data.get('total_sessions', 0) > 0:
                avg_acc = attention_data.get('avg_accuracy', 0)
                best_acc = attention_data.get('best_accuracy', 0)
                st.write(f"- **Total Sessions:** {attention_data.get('total_sessions', 0)}")
                st.write(f"- **Average Accuracy:** {avg_acc * 100:.1f}%" if avg_acc else "- **Average Accuracy:** N/A")
                st.write(f"- **Best Accuracy:** {best_acc * 100:.1f}%" if best_acc else "- **Best Accuracy:** N/A")
                
                # Simple progress bar
                if avg_acc:
                    st.progress(avg_acc, text=f"Average: {avg_acc * 100:.1f}%")
            else:
                st.info("No attention sessions recorded yet.")
        
        with col2:
            st.markdown("#### Visual Memory Module")
            if memory_data.get('total_sessions', 0) > 0:
                avg_acc = memory_data.get('avg_accuracy', 0)
                best_acc = memory_data.get('best_accuracy', 0)
                st.write(f"- **Total Sessions:** {memory_data.get('total_sessions', 0)}")
                st.write(f"- **Average Accuracy:** {avg_acc * 100:.1f}%" if avg_acc else "- **Average Accuracy:** N/A")
                st.write(f"- **Best Accuracy:** {best_acc * 100:.1f}%" if best_acc else "- **Best Accuracy:** N/A")
                
                if avg_acc:
                    st.progress(avg_acc, text=f"Average: {avg_acc * 100:.1f}%")
            else:
                st.info("No memory sessions recorded yet.")
    
    with tab2:
        st.subheader("Attention & Focus Session History")
        _render_exercise_chart("attention", activity_histories.get("attention", []))
        st.markdown("#### Raw sessions")
        st.caption("Teachers/Parents: You can delete individual old records below.")
        
        attention_history = db.get_attention_history(user_id, limit=50)
        
        if attention_history:
            import pandas as pd
            
            for rec in attention_history:
                rid = rec.get("result_id")
                created = rec.get("created_at", "")[:16] if rec.get("created_at") else ""
                acc = rec.get("accuracy")
                acc_str = f"{acc * 100:.1f}%" if acc is not None else "—"
                row1, row2 = st.columns([4, 1])
                with row1:
                    st.write(f"**{created}** — Target: {rec.get('target_letter', '—')} | Correct: {rec.get('correct_clicks', 0)}/{rec.get('total_targets', 0)} | Accuracy: {acc_str} | Time: {rec.get('time_spent_seconds', 0):.0f}s")
                with row2:
                    if st.button("🗑️ Delete", key=f"del_att_{rid}", type="secondary", use_container_width=True):
                        db.delete_attention_result(rid)
                        st.success("Record deleted.")
                        st.rerun()
            st.divider()
            df = pd.DataFrame(attention_history)
            df['accuracy'] = df['accuracy'].apply(lambda x: f"{x * 100:.1f}%" if x is not None else "—")
            df['created_at'] = pd.to_datetime(df['created_at'])
            st.dataframe(
                df[['created_at', 'target_letter', 'correct_clicks', 'total_targets',
                    'accuracy', 'time_spent_seconds', 'age_at_test']].rename(columns={
                    'created_at': 'Date', 'target_letter': 'Target', 'correct_clicks': 'Correct',
                    'total_targets': 'Total', 'accuracy': 'Accuracy',
                    'time_spent_seconds': 'Time (s)', 'age_at_test': 'Age'
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No attention sessions recorded yet.")
    
    with tab3:
        st.subheader("Visual Memory Session History")
        _render_exercise_chart("visual_memory", activity_histories.get("visual_memory", []))
        st.markdown("#### Raw sessions")
        st.caption("Teachers/Parents: You can delete individual old records below.")
        
        memory_history = db.get_visual_memory_history(user_id, limit=50)
        
        if memory_history:
            import pandas as pd
            
            for rec in memory_history:
                rid = rec.get("result_id")
                created = rec.get("created_at", "")[:16] if rec.get("created_at") else ""
                acc = rec.get("accuracy")
                acc_str = f"{acc * 100:.1f}%" if acc is not None else "—"
                row1, row2 = st.columns([4, 1])
                with row1:
                    st.write(f"**{created}** — {rec.get('difficulty_level', '—')} | Grid {rec.get('grid_size', 0)}x{rec.get('grid_size', 0)} | Correct: {rec.get('correct_answers', 0)}/{rec.get('total_questions', 0)} | Accuracy: {acc_str}")
                with row2:
                    if st.button("🗑️ Delete", key=f"del_mem_{rid}", type="secondary", use_container_width=True):
                        db.delete_visual_memory_result(rid)
                        st.success("Record deleted.")
                        st.rerun()
            st.divider()
            df = pd.DataFrame(memory_history)
            df['accuracy'] = df['accuracy'].apply(lambda x: f"{x * 100:.1f}%" if x is not None else "—")
            df['created_at'] = pd.to_datetime(df['created_at'])
            st.dataframe(
                df[['created_at', 'difficulty_level', 'grid_size', 'correct_answers',
                    'total_questions', 'accuracy', 'time_spent_seconds']].rename(columns={
                    'created_at': 'Date', 'difficulty_level': 'Difficulty', 'grid_size': 'Grid',
                    'correct_answers': 'Correct', 'total_questions': 'Total',
                    'accuracy': 'Accuracy', 'time_spent_seconds': 'Time (s)'
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No memory sessions recorded yet.")
    
    with tab4:
        st.subheader("Auditory Memory History")
        _render_exercise_chart("auditory_memory", activity_histories.get("auditory_memory", []))
        st.markdown("#### Raw sessions")
        history = db.get_auditory_memory_history(user_id, limit=50)
        if history:
            import pandas as pd

            for rec in history:
                rid = rec.get("result_id")
                created = rec.get("created_at", "")[:16] if rec.get("created_at") else ""
                acc = rec.get("accuracy")
                acc_str = f"{acc * 100:.1f}%" if acc is not None else "—"
                row1, row2 = st.columns([4, 1])
                with row1:
                    st.write(
                        f"**{created}** — {rec.get('difficulty_level','—')} | "
                        f"max span {rec.get('max_span_reached','—')} | "
                        f"{rec.get('correct_rounds',0)}/{rec.get('total_rounds',0)} rounds | "
                        f"Accuracy: {acc_str}"
                    )
                with row2:
                    if st.button("🗑️ Delete", key=f"del_aud_{rid}",
                                 type="secondary", use_container_width=True):
                        db.delete_auditory_memory_result(rid)
                        st.rerun()
            st.divider()
            df = pd.DataFrame(history)
            df['accuracy'] = df['accuracy'].apply(lambda x: f"{x * 100:.1f}%" if x is not None else "—")
            df['created_at'] = pd.to_datetime(df['created_at'])
            st.dataframe(
                df[['created_at', 'difficulty_level', 'max_span_reached', 'correct_rounds',
                    'total_rounds', 'accuracy', 'time_spent_seconds']].rename(columns={
                    'created_at': 'Date', 'difficulty_level': 'Difficulty',
                    'max_span_reached': 'Max Sequence', 'correct_rounds': 'Correct',
                    'total_rounds': 'Rounds', 'accuracy': 'Accuracy',
                    'time_spent_seconds': 'Time (s)'
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No auditory memory sessions yet.")

    with tab5:
        st.subheader("Working Memory (Digit Span) History")
        _render_exercise_chart("working_memory", activity_histories.get("working_memory", []))
        st.markdown("#### Raw sessions")
        history = db.get_working_memory_history(user_id, limit=50)
        if history:
            import pandas as pd

            for rec in history:
                rid = rec.get("result_id")
                created = rec.get("created_at", "")[:16] if rec.get("created_at") else ""
                acc = rec.get("accuracy")
                acc_str = f"{acc * 100:.1f}%" if acc is not None else "—"
                row1, row2 = st.columns([4, 1])
                with row1:
                    st.write(
                        f"**{created}** — {rec.get('mode','—')} | "
                        f"max span {rec.get('max_span_reached','—')} | "
                        f"{rec.get('correct_trials',0)}/{rec.get('total_trials',0)} trials | "
                        f"Accuracy: {acc_str}"
                    )
                with row2:
                    if st.button("🗑️ Delete", key=f"del_wm_{rid}",
                                 type="secondary", use_container_width=True):
                        db.delete_working_memory_result(rid)
                        st.rerun()
            st.divider()
            df = pd.DataFrame(history)
            df['accuracy'] = df['accuracy'].apply(lambda x: f"{x * 100:.1f}%" if x is not None else "—")
            df['created_at'] = pd.to_datetime(df['created_at'])
            st.dataframe(
                df[['created_at', 'mode', 'max_span_reached', 'correct_trials',
                    'total_trials', 'accuracy', 'time_spent_seconds']].rename(columns={
                    'created_at': 'Date', 'mode': 'Mode',
                    'max_span_reached': 'Max Sequence', 'correct_trials': 'Correct',
                    'total_trials': 'Trials', 'accuracy': 'Accuracy',
                    'time_spent_seconds': 'Time (s)'
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No working memory sessions yet.")

    with tab6:
        st.subheader("Processing Speed History")
        _render_exercise_chart("processing_speed", activity_histories.get("processing_speed", []))
        st.markdown("#### Raw sessions")
        history = db.get_processing_speed_history(user_id, limit=50)
        if history:
            import pandas as pd

            for rec in history:
                rid = rec.get("result_id")
                created = rec.get("created_at", "")[:16] if rec.get("created_at") else ""
                acc = rec.get("accuracy")
                acc_str = f"{acc * 100:.1f}%" if acc is not None else "—"
                rt = rec.get("avg_reaction_ms") or 0
                row1, row2 = st.columns([4, 1])
                with row1:
                    st.write(
                        f"**{created}** — {rec.get('task_type','—')} / "
                        f"{rec.get('difficulty_level','—')} | "
                        f"{rec.get('correct_trials',0)}/{rec.get('total_trials',0)} trials | "
                        f"Accuracy: {acc_str} | Avg RT: {rt/1000:.2f}s"
                    )
                with row2:
                    if st.button("🗑️ Delete", key=f"del_ps_{rid}",
                                 type="secondary", use_container_width=True):
                        db.delete_processing_speed_result(rid)
                        st.rerun()
            st.divider()
            df = pd.DataFrame(history)
            df['accuracy'] = df['accuracy'].apply(lambda x: f"{x * 100:.1f}%" if x is not None else "—")
            df['avg_reaction_ms'] = df['avg_reaction_ms'].apply(lambda x: f"{(x or 0)/1000:.2f}s")
            df['created_at'] = pd.to_datetime(df['created_at'])
            st.dataframe(
                df[['created_at', 'task_type', 'difficulty_level', 'correct_trials',
                    'total_trials', 'accuracy', 'avg_reaction_ms']].rename(columns={
                    'created_at': 'Date', 'task_type': 'Task',
                    'difficulty_level': 'Difficulty', 'correct_trials': 'Correct',
                    'total_trials': 'Trials', 'accuracy': 'Accuracy',
                    'avg_reaction_ms': 'Avg Reaction'
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No processing speed sessions yet.")

    with tab7:
        st.subheader("Final Assessment Reports")
        _render_exercise_chart("final_assessment", activity_histories.get("final_assessment", []))
        st.markdown("#### Raw sessions")
        history = db.get_final_assessment_history(user_id, limit=20)
        if history:
            import pandas as pd

            for rec in history:
                rid = rec.get("result_id")
                created = rec.get("created_at", "")[:16] if rec.get("created_at") else ""
                row1, row2 = st.columns([4, 1])
                with row1:
                    st.markdown(
                        f"**{created}** — Overall **{rec.get('overall_score',0):.0f}/100**  \n"
                        f"🎯 {rec.get('attention_score',0):.0f} • "
                        f"🧩 {rec.get('visual_memory_score',0):.0f} • "
                        f"🔊 {rec.get('auditory_memory_score',0):.0f} • "
                        f"🔢 {rec.get('working_memory_score',0):.0f} • "
                        f"⚡ {rec.get('processing_speed_score',0):.0f}"
                    )
                    if rec.get("summary"):
                        st.caption(rec["summary"])
                with row2:
                    if st.button("🗑️ Delete", key=f"del_fa_{rid}",
                                 type="secondary", use_container_width=True):
                        db.delete_final_assessment_result(rid)
                        st.rerun()
            st.divider()
            df = pd.DataFrame(history)
            df['created_at'] = pd.to_datetime(df['created_at'])
            st.dataframe(
                df[['created_at', 'overall_score', 'attention_score', 'visual_memory_score',
                    'auditory_memory_score', 'working_memory_score', 'processing_speed_score',
                    'time_spent_seconds']].rename(columns={
                    'created_at': 'Date', 'overall_score': 'Total Score',
                    'attention_score': 'Focus', 'visual_memory_score': 'Visual Memory',
                    'auditory_memory_score': 'Auditory Memory',
                    'working_memory_score': 'Working Memory',
                    'processing_speed_score': 'Processing Speed',
                    'time_spent_seconds': 'Time (s)'
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No final assessments yet.")

    st.divider()
    
    # Export section
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export All Progress to CSV", use_container_width=True):
            all_data = db.export_user_data(user_id)
            
            import pandas as pd
            import json
            
            # Create combined CSV
            export_data = []
            
            for record in all_data.get('attention_history', []):
                export_data.append({
                    'module': 'attention',
                    'date': record.get('created_at'),
                    'accuracy': record.get('accuracy'),
                    'time_seconds': record.get('time_spent_seconds'),
                    'details': f"Target: {record.get('target_letter')}, Correct: {record.get('correct_clicks')}/{record.get('total_targets')}"
                })
            
            for record in all_data.get('visual_memory_history', []):
                export_data.append({
                    'module': 'visual_memory',
                    'date': record.get('created_at'),
                    'accuracy': record.get('accuracy'),
                    'time_seconds': record.get('time_spent_seconds'),
                    'details': f"Grid: {record.get('grid_size')}x{record.get('grid_size')}, Score: {record.get('correct_answers')}/{record.get('total_questions')}"
                })

            for record in all_data.get('auditory_memory_history', []):
                export_data.append({
                    'module': 'auditory_memory',
                    'date': record.get('created_at'),
                    'accuracy': record.get('accuracy'),
                    'time_seconds': record.get('time_spent_seconds'),
                    'details': (
                        f"Difficulty: {record.get('difficulty_level')}, "
                        f"Max span: {record.get('max_span_reached')}, "
                        f"Score: {record.get('correct_rounds')}/{record.get('total_rounds')}"
                    ),
                })

            for record in all_data.get('working_memory_history', []):
                export_data.append({
                    'module': 'working_memory',
                    'date': record.get('created_at'),
                    'accuracy': record.get('accuracy'),
                    'time_seconds': record.get('time_spent_seconds'),
                    'details': (
                        f"Mode: {record.get('mode')}, "
                        f"Max span: {record.get('max_span_reached')}, "
                        f"Score: {record.get('correct_trials')}/{record.get('total_trials')}"
                    ),
                })

            for record in all_data.get('processing_speed_history', []):
                export_data.append({
                    'module': 'processing_speed',
                    'date': record.get('created_at'),
                    'accuracy': record.get('accuracy'),
                    'time_seconds': record.get('time_spent_seconds'),
                    'details': (
                        f"Task: {record.get('task_type')}/"
                        f"{record.get('difficulty_level')}, "
                        f"Score: {record.get('correct_trials')}/{record.get('total_trials')}, "
                        f"Avg RT: {(record.get('avg_reaction_ms') or 0)/1000:.2f}s"
                    ),
                })

            for record in all_data.get('final_assessment_history', []):
                export_data.append({
                    'module': 'final_assessment',
                    'date': record.get('created_at'),
                    'accuracy': (record.get('overall_score') or 0) / 100.0,
                    'time_seconds': record.get('time_spent_seconds'),
                    'details': (
                        f"Overall {record.get('overall_score',0):.0f}/100 — "
                        f"att {record.get('attention_score',0):.0f}, "
                        f"vm {record.get('visual_memory_score',0):.0f}, "
                        f"am {record.get('auditory_memory_score',0):.0f}, "
                        f"wm {record.get('working_memory_score',0):.0f}, "
                        f"ps {record.get('processing_speed_score',0):.0f}"
                    ),
                })
            
            if export_data:
                df = pd.DataFrame(export_data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"child_progress_{user_id}.csv",
                    "text/csv",
                    use_container_width=True
                )
            else:
                st.warning("No data to export yet.")


def main():
    """Main application entry point."""
    load_accessibility_css()
    apply_theme()
    
    # Initialize mode selection
    if 'mode_selected' not in st.session_state:
        st.session_state.mode_selected = False
    
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = "child"

    if 'teacher_authenticated' not in st.session_state:
        st.session_state.teacher_authenticated = False
    
    # Show mode selector if not selected
    if not st.session_state.mode_selected:
        show_mode_selector()
    else:
        # Show appropriate home screen
        if st.session_state.app_mode == "child":
            show_child_home()
        else:
            if st.session_state.teacher_authenticated:
                show_teacher_home()
            else:
                show_teacher_login()


if __name__ == "__main__":
    main()
