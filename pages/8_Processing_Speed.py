"""
Processing Speed Module — Fully Implemented

Three sub-tasks (the player picks one per session):

1. Same / Different  — pairs of letters (incl. confusable b/d/p/q).
2. Color Match       — Stroop-style: word vs ink color.
3. Pattern Spot      — pick the shape that does NOT match the rest.

Each session is N trials. We measure accuracy and average reaction time, and
store everything via DatabaseHandler.record_processing_speed_result.
"""

import os
import sys
import time
import random
import string

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import SessionManager
from utils.theme import apply_theme, render_theme_toggle
from database.db_handler import DatabaseHandler

SessionManager.initialize_session()
SessionManager.track_page_visit("processing_speed")

st.set_page_config(page_title="Quick Think Game", page_icon="⚡", layout="wide")
apply_theme()


# ---------------------------------------------------------------------------
# Page-local CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
.ps-title { font-size: 2.4rem; text-align: center; margin: 0.4rem 0 1rem 0; }
.ps-stage {
    background: var(--app-panel);
    border: 3px solid var(--app-border);
    border-radius: 24px;
    padding: 2.2rem 1rem;
    text-align: center;
    box-shadow: var(--app-shadow);
    min-height: 220px;
    display: flex; align-items: center; justify-content: center;
}
.ps-letters { font-size: 6rem; font-weight: 800; letter-spacing: 0.4em; }
.ps-stroop  { font-size: 5rem; font-weight: 800; letter-spacing: 0.15em; }
.ps-pill {
    display: inline-block;
    padding: 0.4rem 1rem;
    border-radius: 999px;
    background: var(--app-panel-alt);
    border: 1px solid var(--app-border);
    font-weight: 600;
}
.ps-feedback-ok  { color: var(--app-success); font-weight: 700; font-size: 1.4rem; text-align: center; }
.ps-feedback-bad { color: var(--app-danger);  font-weight: 700; font-size: 1.4rem; text-align: center; }
.ps-shape {
    width: 130px; height: 130px;
    margin: 0 auto;
    box-shadow: var(--app-shadow);
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFUSABLE_PAIRS = [
    ("b", "d"), ("p", "q"), ("m", "n"), ("u", "v"), ("a", "e"),
    ("c", "o"), ("h", "n"), ("i", "l"), ("f", "t"),
]
COLOR_NAMES = {
    "RED":   "#E53935",
    "BLUE":  "#1E88E5",
    "GREEN": "#43A047",
    "YELLOW": "#FBC02D",
    "PURPLE": "#8E24AA",
    "ORANGE": "#FB8C00",
}
SHAPES = ["circle", "square", "triangle", "diamond"]


# ---------------------------------------------------------------------------
# Trial generators
# ---------------------------------------------------------------------------

def make_same_diff_trial(difficulty: str) -> dict:
    """Two letters; player decides Same / Different."""
    use_confusable = difficulty != "easy" and random.random() < 0.5
    same = random.random() < 0.5

    if same:
        letter = random.choice(string.ascii_lowercase)
        a, b = letter, letter
    else:
        if use_confusable:
            a, b = random.choice(CONFUSABLE_PAIRS)
            if random.random() < 0.5:
                a, b = b, a
        else:
            a = random.choice(string.ascii_lowercase)
            b = random.choice([x for x in string.ascii_lowercase if x != a])
    return {
        "type": "same_diff",
        "letters": (a, b),
        "answer": "same" if same else "different",
    }


def make_color_match_trial(difficulty: str) -> dict:
    """Stroop: a color word printed in some ink. Player picks the INK color."""
    word = random.choice(list(COLOR_NAMES.keys()))
    if difficulty == "easy" or random.random() < 0.3:
        ink = word
    else:
        ink = random.choice([c for c in COLOR_NAMES if c != word])
    return {
        "type": "color_match",
        "word": word,
        "ink": ink,
        "answer": ink,
    }


def make_pattern_trial(difficulty: str) -> dict:
    """4 shapes: 3 the same, 1 different. Player picks the odd one out."""
    base_shape = random.choice(SHAPES)
    odd_shape = random.choice([s for s in SHAPES if s != base_shape])
    color = random.choice(list(COLOR_NAMES.values()))

    n_options = 4
    odd_pos = random.randint(0, n_options - 1)
    options = []
    for i in range(n_options):
        options.append(odd_shape if i == odd_pos else base_shape)
    return {
        "type": "pattern",
        "options": options,
        "color": color,
        "answer": odd_pos,
    }


def make_trial(task_type: str, difficulty: str) -> dict:
    return {
        "same_diff":     make_same_diff_trial,
        "color_match":   make_color_match_trial,
        "pattern":       make_pattern_trial,
    }[task_type](difficulty)


def difficulty_settings(level: str) -> dict:
    return {
        "easy":   {"trials": 8,  "max_seconds": 8.0},
        "medium": {"trials": 10, "max_seconds": 5.0},
        "hard":   {"trials": 12, "max_seconds": 3.0},
    }.get(level, {"trials": 8, "max_seconds": 8.0})


# ---------------------------------------------------------------------------
# Shape rendering
# ---------------------------------------------------------------------------

def shape_html(shape: str, color: str) -> str:
    if shape == "circle":
        return f'<div class="ps-shape" style="background:{color}; border-radius:50%;"></div>'
    if shape == "square":
        return f'<div class="ps-shape" style="background:{color}; border-radius:14px;"></div>'
    if shape == "triangle":
        return (
            '<div class="ps-shape" style="'
            'width:0;height:0;background:transparent;'
            f'border-left:65px solid transparent;border-right:65px solid transparent;'
            f'border-bottom:130px solid {color};box-shadow:none;"></div>'
        )
    if shape == "diamond":
        return (
            f'<div class="ps-shape" style="background:{color}; '
            'border-radius:14px; transform:rotate(45deg);"></div>'
        )
    return f'<div class="ps-shape" style="background:{color};"></div>'


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def init_state():
    ss = st.session_state
    ss.setdefault("ps_phase", "setup")           # setup | trial | feedback | results
    ss.setdefault("ps_task", "same_diff")
    ss.setdefault("ps_difficulty", "easy")
    ss.setdefault("ps_trial_index", 0)
    ss.setdefault("ps_trials_total", 8)
    ss.setdefault("ps_trial", None)
    ss.setdefault("ps_trial_started", None)
    ss.setdefault("ps_correct", 0)
    ss.setdefault("ps_reaction_times_ms", [])
    ss.setdefault("ps_start_time", None)
    ss.setdefault("ps_last_correct", None)
    ss.setdefault("ps_last_rt_ms", None)


def reset_state():
    for k in [
        "ps_phase", "ps_trial_index", "ps_trials_total", "ps_trial",
        "ps_trial_started", "ps_correct", "ps_reaction_times_ms",
        "ps_start_time", "ps_last_correct", "ps_last_rt_ms",
    ]:
        st.session_state.pop(k, None)
    init_state()


init_state()


def grade(answer) -> None:
    """Mark current trial and advance to feedback phase."""
    rt_ms = (time.time() - st.session_state.ps_trial_started) * 1000.0
    correct = answer == st.session_state.ps_trial["answer"]
    if correct:
        st.session_state.ps_correct += 1
    st.session_state.ps_reaction_times_ms.append(rt_ms)
    st.session_state.ps_last_correct = correct
    st.session_state.ps_last_rt_ms = rt_ms
    st.session_state.ps_phase = "feedback"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

db = DatabaseHandler()
user_id = SessionManager.get_user_id()
user_name = SessionManager.get_user_name() or "Friend"
is_child_mode = st.session_state.get("app_mode", "child") == "child"

with st.sidebar:
    st.markdown(f"### 👋 Hi, {user_name}!")
    st.markdown(f"### ⭐ Stars: {db.get_total_stars(user_id)}")
    st.divider()
    render_theme_toggle(location="sidebar", key_suffix="ps")
    st.divider()
    if st.button("🏠 Go Home", use_container_width=True, key="ps_home"):
        reset_state()
        st.switch_page("app.py")
    if st.button("🎮 All Games", use_container_width=True, key="ps_all"):
        reset_state()
        st.switch_page("pages/3_Learning_Support.py")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

st.markdown('<p class="ps-title">⚡ Quick Think Game</p>', unsafe_allow_html=True)

phase = st.session_state.ps_phase

# ===== Setup =====
if phase == "setup":
    st.markdown(
        f"""
        <div class="instruction-box">
            <strong>👋 Hi {user_name}!</strong><br><br>
            <strong>⚡ How to play:</strong><br>
            Answer as <em>fast</em> as you can — but try to be right!
            We measure both how often you answer correctly <strong>and</strong>
            how fast you do it.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🎯 Pick a task")
    cols = st.columns(3)
    options = [
        ("same_diff",   "🔤 Same / Different", "Are these two letters the same?"),
        ("color_match", "🎨 Color Match",      "Pick the INK color, not the word."),
        ("pattern",     "🔍 Pattern Spot",     "Click the shape that's different."),
    ]
    for col, (tid, label, desc) in zip(cols, options):
        with col:
            if st.button(f"{label}\n{desc}", key=f"ps_pick_{tid}", use_container_width=True,
                         type="primary" if st.session_state.ps_task == tid else "secondary"):
                st.session_state.ps_task = tid
                st.rerun()

    st.markdown("### 🎚 Difficulty")
    dcols = st.columns(3)
    for col, lvl in zip(dcols, ["easy", "medium", "hard"]):
        with col:
            if st.button(f"{lvl.capitalize()}", key=f"ps_diff_{lvl}",
                         use_container_width=True,
                         type="primary" if st.session_state.ps_difficulty == lvl else "secondary"):
                st.session_state.ps_difficulty = lvl
                st.rerun()

    cfg = difficulty_settings(st.session_state.ps_difficulty)
    st.info(
        f"**Task:** {st.session_state.ps_task.replace('_',' ').title()} • "
        f"**Difficulty:** {st.session_state.ps_difficulty.upper()} • "
        f"**Trials:** {cfg['trials']}"
    )

    if st.button("🚀 Start", type="primary", use_container_width=True, key="ps_start"):
        cfg = difficulty_settings(st.session_state.ps_difficulty)
        st.session_state.ps_trials_total = cfg["trials"]
        st.session_state.ps_trial_index = 0
        st.session_state.ps_correct = 0
        st.session_state.ps_reaction_times_ms = []
        st.session_state.ps_start_time = time.time()
        st.session_state.ps_trial = make_trial(
            st.session_state.ps_task, st.session_state.ps_difficulty
        )
        st.session_state.ps_trial_started = time.time()
        st.session_state.ps_phase = "trial"
        st.rerun()

# ===== Trial =====
elif phase == "trial":
    trial = st.session_state.ps_trial
    cfg = difficulty_settings(st.session_state.ps_difficulty)
    elapsed = time.time() - st.session_state.ps_trial_started
    remaining = cfg["max_seconds"] - elapsed
    if remaining <= 0:
        # Treat timeout as wrong answer with full RT
        st.session_state.ps_reaction_times_ms.append(cfg["max_seconds"] * 1000.0)
        st.session_state.ps_last_correct = False
        st.session_state.ps_last_rt_ms = cfg["max_seconds"] * 1000.0
        st.session_state.ps_phase = "feedback"
        st.rerun()

    st.markdown(
        f'<div style="text-align:center"><span class="ps-pill">'
        f'Trial {st.session_state.ps_trial_index + 1} / {st.session_state.ps_trials_total} • '
        f'⏳ {remaining:0.1f}s</span></div>',
        unsafe_allow_html=True,
    )

    if trial["type"] == "same_diff":
        a, b = trial["letters"]
        st.markdown(
            f'<div class="ps-stage"><div class="ps-letters">{a}&nbsp;&nbsp;&nbsp;{b}</div></div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Same", use_container_width=True, type="primary", key="ps_ans_same"):
                grade("same")
                st.rerun()
        with c2:
            if st.button("❌ Different", use_container_width=True, type="primary", key="ps_ans_diff"):
                grade("different")
                st.rerun()

    elif trial["type"] == "color_match":
        ink_color = COLOR_NAMES[trial["ink"]]
        st.markdown(
            f"""
            <div class="ps-stage">
                <div class="ps-stroop" style="color:{ink_color};">
                    {trial['word']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; font-size:1.1rem;'>"
            "Click the colour the word is <strong>painted in</strong> (not what the word says).</p>",
            unsafe_allow_html=True,
        )
        # Build a randomized 6-option grid
        names = list(COLOR_NAMES.keys())
        random.Random(trial["word"] + trial["ink"]).shuffle(names)
        rows = [names[:3], names[3:]]
        for row in rows:
            cols = st.columns(3)
            for c, name in zip(cols, row):
                with c:
                    if st.button(name, use_container_width=True, key=f"ps_col_{name}"):
                        grade(name)
                        st.rerun()

    elif trial["type"] == "pattern":
        st.markdown(
            "<p style='text-align:center; font-size:1.1rem;'>"
            "Find the shape that's <strong>different</strong>!</p>",
            unsafe_allow_html=True,
        )
        cols = st.columns(len(trial["options"]))
        for i, shape in enumerate(trial["options"]):
            with cols[i]:
                st.markdown(shape_html(shape, trial["color"]), unsafe_allow_html=True)
                if st.button(f"Pick #{i+1}", use_container_width=True, key=f"ps_shape_{i}"):
                    grade(i)
                    st.rerun()

    # Auto-refresh while in trial so the timer counts down
    time.sleep(0.2)
    st.rerun()

# ===== Feedback =====
elif phase == "feedback":
    correct = st.session_state.ps_last_correct
    rt = st.session_state.ps_last_rt_ms or 0
    if correct:
        st.markdown(
            f'<p class="ps-feedback-ok">✅ Correct! ({rt/1000:.2f}s)</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<p class="ps-feedback-bad">❌ Not quite ({rt/1000:.2f}s)</p>',
            unsafe_allow_html=True,
        )

    done = st.session_state.ps_trial_index + 1 >= st.session_state.ps_trials_total

    c1, c2, c3 = st.columns(3)
    c1.metric("Trial", f"{st.session_state.ps_trial_index + 1} / {st.session_state.ps_trials_total}")
    c2.metric("Correct", st.session_state.ps_correct)
    if st.session_state.ps_reaction_times_ms:
        avg_rt = sum(st.session_state.ps_reaction_times_ms) / len(st.session_state.ps_reaction_times_ms)
        c3.metric("Avg RT (s)", f"{avg_rt/1000:.2f}")

    if done:
        if st.button("🏁 See my results", type="primary",
                     use_container_width=True, key="ps_finish"):
            st.session_state.ps_phase = "results"
            st.rerun()
    else:
        if st.button("➡ Next", type="primary", use_container_width=True, key="ps_next"):
            st.session_state.ps_trial_index += 1
            st.session_state.ps_trial = make_trial(
                st.session_state.ps_task, st.session_state.ps_difficulty
            )
            st.session_state.ps_trial_started = time.time()
            st.session_state.ps_phase = "trial"
            st.rerun()

# ===== Results =====
elif phase == "results":
    total = st.session_state.ps_trials_total
    correct = st.session_state.ps_correct
    accuracy = correct / max(total, 1)
    elapsed = time.time() - (st.session_state.ps_start_time or time.time())
    rts = st.session_state.ps_reaction_times_ms
    avg_rt = sum(rts) / len(rts) if rts else 0.0
    stars = db.calculate_stars_for_accuracy(accuracy)
    star_icons = "⭐" * stars

    st.markdown(
        f"""
        <div class="encouragement">
            ⚡ Lightning fast, {user_name}! You earned {star_icons} ({stars} stars).
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Task", st.session_state.ps_task.replace("_", " ").title())
    c2.metric("Correct", f"{correct} / {total}")
    c3.metric("Accuracy", f"{accuracy*100:.0f}%")
    c4.metric("Avg RT", f"{avg_rt/1000:.2f}s")

    db.record_processing_speed_result(
        user_id=user_id,
        task_type=st.session_state.ps_task,
        total_trials=total,
        correct_trials=correct,
        accuracy=accuracy,
        avg_reaction_ms=avg_rt,
        time_spent_seconds=elapsed,
        difficulty_level=st.session_state.ps_difficulty,
    )
    db.record_session(
        user_id=user_id,
        module_name="processing_speed",
        accuracy=accuracy,
        time_spent_seconds=elapsed,
        score=correct,
        max_score=total,
    )
    db.award_stars(
        user_id=user_id,
        module_name="processing_speed",
        stars=stars,
        reason=f"Quick think ({st.session_state.ps_task}/{st.session_state.ps_difficulty}) - {accuracy*100:.0f}%",
    )

    st.markdown("---")
    n1, n2, n3 = st.columns(3)
    with n1:
        if st.button("🔄 Play again", type="primary", use_container_width=True, key="ps_again"):
            reset_state()
            st.rerun()
    with n2:
        if st.button("🏆 Final Challenge", use_container_width=True, key="ps_to_final"):
            reset_state()
            st.switch_page("pages/9_Final_Assessment.py")
    with n3:
        if st.button("🏠 Home", use_container_width=True, key="ps_to_home"):
            reset_state()
            st.switch_page("app.py")

# Teacher mode
if not is_child_mode:
    st.divider()
    st.markdown("### 👨‍🏫 Teacher / Parent notes")
    st.write(
        "Processing speed combines **accuracy** with **reaction time**. Slower "
        "RTs with similar accuracy can hint at processing-speed weaknesses; "
        "lower accuracy with fast RTs suggests impulsivity."
    )
    history = db.get_processing_speed_history(user_id, limit=10)
    if history:
        st.markdown("Recent sessions:")
        for h in history:
            acc = h.get("accuracy") or 0
            rt = h.get("avg_reaction_ms") or 0
            st.write(
                f"- {h.get('created_at','')[:16]} — "
                f"{h.get('task_type','?')}/{h.get('difficulty_level','?')} • "
                f"{acc*100:.0f}% • {rt/1000:.2f}s avg RT"
            )
