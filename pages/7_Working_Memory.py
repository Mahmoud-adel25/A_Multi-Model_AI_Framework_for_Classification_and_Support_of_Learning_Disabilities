"""
Working Memory Module — Fully Implemented (Digit Span Forward / Backward)

Phases:
  setup    -> player picks mode + starting span
  show     -> digits flash one at a time
  recall   -> player types them back (forward or reversed)
  feedback -> result of the trial; adaptive next span
  results  -> session summary stored in DB
"""

import os
import sys
import time
import random

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import SessionManager
from utils.theme import apply_theme, render_theme_toggle
from database.db_handler import DatabaseHandler

SessionManager.initialize_session()
SessionManager.track_page_visit("working_memory")

st.set_page_config(page_title="Number Memory Game", page_icon="🔢", layout="wide")
apply_theme()


# ---------------------------------------------------------------------------
# Page-local CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
.wm-title { font-size: 2.4rem; text-align: center; margin: 0.4rem 0 1rem 0; }
.wm-digit-stage {
    background: var(--app-panel);
    border: 3px solid var(--app-border);
    border-radius: 24px;
    padding: 2.5rem 1rem;
    text-align: center;
    box-shadow: var(--app-shadow);
    min-height: 220px;
    display: flex; align-items: center; justify-content: center;
}
.wm-digit {
    font-size: 7rem;
    font-weight: 800;
    color: var(--app-accent);
    letter-spacing: 0.15em;
    line-height: 1;
}
.wm-pill {
    display: inline-block;
    padding: 0.4rem 1rem;
    border-radius: 999px;
    background: var(--app-panel-alt);
    border: 1px solid var(--app-border);
    font-weight: 600;
}
.wm-keypad button {
    font-size: 1.8rem !important;
    padding: 1rem 0 !important;
    border-radius: 16px !important;
    min-height: 70px !important;
}
.wm-feedback-ok   { color: var(--app-success); font-weight: 700; font-size: 1.4rem; text-align: center; }
.wm-feedback-bad  { color: var(--app-danger);  font-weight: 700; font-size: 1.4rem; text-align: center; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def init_state():
    ss = st.session_state
    ss.setdefault("wm_phase", "setup")           # setup | show | recall | feedback | results
    ss.setdefault("wm_mode", "forward")          # forward | backward
    ss.setdefault("wm_span", 3)
    ss.setdefault("wm_max_span", 8)
    ss.setdefault("wm_max_trials", 8)
    ss.setdefault("wm_digits", [])
    ss.setdefault("wm_show_index", 0)
    ss.setdefault("wm_show_started_at", None)
    ss.setdefault("wm_per_digit_seconds", 1.0)
    ss.setdefault("wm_typed", "")
    ss.setdefault("wm_total_trials", 0)
    ss.setdefault("wm_correct_trials", 0)
    ss.setdefault("wm_max_span_reached", 0)
    ss.setdefault("wm_start_time", None)
    ss.setdefault("wm_last_was_correct", None)
    ss.setdefault("wm_consecutive_wrong", 0)


def reset_state():
    for k in [
        "wm_phase", "wm_mode", "wm_span", "wm_digits", "wm_show_index",
        "wm_show_started_at", "wm_typed", "wm_total_trials", "wm_correct_trials",
        "wm_max_span_reached", "wm_start_time", "wm_last_was_correct",
        "wm_consecutive_wrong",
    ]:
        st.session_state.pop(k, None)
    init_state()


init_state()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def new_digits(span: int) -> list:
    """Random digits 0-9, no two adjacent same digits to keep it readable."""
    digits = []
    while len(digits) < span:
        d = random.randint(0, 9)
        if not digits or digits[-1] != d:
            digits.append(d)
    return digits


def expected_answer(digits: list, mode: str) -> str:
    seq = digits if mode == "forward" else list(reversed(digits))
    return "".join(str(d) for d in seq)


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
    render_theme_toggle(location="sidebar", key_suffix="wm")
    st.divider()
    if st.button("🏠 Go Home", use_container_width=True, key="wm_home"):
        reset_state()
        st.switch_page("app.py")
    if st.button("🎮 All Games", use_container_width=True, key="wm_all"):
        reset_state()
        st.switch_page("pages/3_Learning_Support.py")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

st.markdown('<p class="wm-title">🔢 Number Memory Game</p>', unsafe_allow_html=True)

phase = st.session_state.wm_phase

# ===== Setup =====
if phase == "setup":
    st.markdown(
        f"""
        <div class="instruction-box">
            <strong>👋 Hi {user_name}!</strong><br><br>
            <strong>🎯 How to play:</strong><br>
            1. The game shows you a few numbers, one at a time.<br>
            2. When they're done, type them back.<br>
            3. <em>Forward</em> mode = same order. <em>Backward</em> mode = reverse order!
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Mode")
        if st.button("➡️ Forward (same order)", use_container_width=True,
                     key="wm_pick_fwd",
                     type="primary" if st.session_state.wm_mode == "forward" else "secondary"):
            st.session_state.wm_mode = "forward"
            st.rerun()
        if st.button("⬅️ Backward (reverse order)", use_container_width=True,
                     key="wm_pick_bwd",
                     type="primary" if st.session_state.wm_mode == "backward" else "secondary"):
            st.session_state.wm_mode = "backward"
            st.rerun()

    with c2:
        st.markdown("#### Starting length")
        st.session_state.wm_span = st.select_slider(
            "How many numbers to remember at first?",
            options=[3, 4, 5, 6, 7, 8],
            value=st.session_state.wm_span,
        )
        st.session_state.wm_per_digit_seconds = st.select_slider(
            "Speed (seconds per number)",
            options=[0.6, 0.8, 1.0, 1.2, 1.5],
            value=st.session_state.wm_per_digit_seconds,
        )

    if st.button("🚀 Start", type="primary", use_container_width=True, key="wm_start"):
        st.session_state.wm_digits = new_digits(st.session_state.wm_span)
        st.session_state.wm_show_index = 0
        st.session_state.wm_show_started_at = time.time()
        st.session_state.wm_typed = ""
        st.session_state.wm_total_trials = 0
        st.session_state.wm_correct_trials = 0
        st.session_state.wm_max_span_reached = st.session_state.wm_span
        st.session_state.wm_start_time = time.time()
        st.session_state.wm_consecutive_wrong = 0
        st.session_state.wm_phase = "show"
        st.rerun()

# ===== Show =====
elif phase == "show":
    digits = st.session_state.wm_digits
    per = st.session_state.wm_per_digit_seconds
    total_show_time = per * len(digits)
    elapsed = time.time() - st.session_state.wm_show_started_at
    idx = int(elapsed // per)

    st.markdown(
        f'<div style="text-align:center"><span class="wm-pill">'
        f'{st.session_state.wm_mode.capitalize()} • {len(digits)} digits'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    if elapsed >= total_show_time:
        st.session_state.wm_typed = ""
        st.session_state.wm_phase = "recall"
        st.rerun()
    else:
        digit = digits[min(idx, len(digits) - 1)]
        st.markdown(
            f'<div class="wm-digit-stage"><div class="wm-digit">{digit}</div></div>',
            unsafe_allow_html=True,
        )
        remaining = max(int(total_show_time - elapsed) + 1, 1)
        st.markdown(
            f'<div style="text-align:center; color:var(--app-muted); margin-top:0.7rem;">'
            f'Pay attention… {remaining}s left</div>',
            unsafe_allow_html=True,
        )
        time.sleep(0.2)
        st.rerun()

# ===== Recall =====
elif phase == "recall":
    digits = st.session_state.wm_digits
    typed = st.session_state.wm_typed

    if st.session_state.wm_mode == "forward":
        prompt = "Type the numbers in the **same order** you saw them."
    else:
        prompt = "Type the numbers in the **REVERSE order** (last one first)."

    st.markdown(
        f'<div style="text-align:center"><span class="wm-pill">'
        f'{st.session_state.wm_mode.capitalize()} mode • {len(digits)} digits'
        f'</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"<p style='text-align:center; font-size:1.2rem;'>{prompt}</p>",
                unsafe_allow_html=True)

    st.markdown(
        f'<div class="wm-digit-stage"><div class="wm-digit">'
        f'{typed if typed else "&nbsp;"}'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    keypad_layout = [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
        ["⌫", "0", "✓"],
    ]

    st.markdown('<div class="wm-keypad">', unsafe_allow_html=True)
    for row in keypad_layout:
        cols = st.columns(3)
        for c, label in zip(cols, row):
            with c:
                if st.button(label, use_container_width=True, key=f"wm_k_{label}_{len(typed)}"):
                    if label == "⌫":
                        st.session_state.wm_typed = typed[:-1]
                        st.rerun()
                    elif label == "✓":
                        if not typed:
                            st.warning("Please type something first.")
                        else:
                            expected = expected_answer(digits, st.session_state.wm_mode)
                            ok = typed == expected
                            st.session_state.wm_total_trials += 1
                            if ok:
                                st.session_state.wm_correct_trials += 1
                                st.session_state.wm_max_span_reached = max(
                                    st.session_state.wm_max_span_reached, len(digits)
                                )
                                st.session_state.wm_consecutive_wrong = 0
                            else:
                                st.session_state.wm_consecutive_wrong += 1
                            st.session_state.wm_last_was_correct = ok
                            st.session_state.wm_phase = "feedback"
                            st.rerun()
                    else:
                        if len(typed) < len(digits):
                            st.session_state.wm_typed = typed + label
                            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    cleft, cright = st.columns(2)
    with cleft:
        if st.button("↩ Clear", use_container_width=True, key="wm_clear"):
            st.session_state.wm_typed = ""
            st.rerun()
    with cright:
        if st.button("👀 Show again", use_container_width=True, key="wm_replay"):
            st.session_state.wm_show_index = 0
            st.session_state.wm_show_started_at = time.time()
            st.session_state.wm_phase = "show"
            st.rerun()

# ===== Feedback =====
elif phase == "feedback":
    digits = st.session_state.wm_digits
    expected = expected_answer(digits, st.session_state.wm_mode)
    typed = st.session_state.wm_typed
    ok = st.session_state.wm_last_was_correct

    if ok:
        st.markdown('<p class="wm-feedback-ok">✅ Correct! Amazing memory!</p>',
                    unsafe_allow_html=True)
        st.balloons()
    else:
        st.markdown(
            f'<p class="wm-feedback-bad">❌ Not quite — the answer was '
            f'<strong>{" ".join(expected)}</strong> (you typed <strong>{typed}</strong>).</p>',
            unsafe_allow_html=True,
        )

    c1, c2, c3 = st.columns(3)
    c1.metric("Trial", f"{st.session_state.wm_total_trials} / {st.session_state.wm_max_trials}")
    c2.metric("Correct", st.session_state.wm_correct_trials)
    c3.metric("Best span", st.session_state.wm_max_span_reached)

    done_trials = st.session_state.wm_total_trials >= st.session_state.wm_max_trials
    bail_out = st.session_state.wm_consecutive_wrong >= 2

    if done_trials or bail_out:
        if st.button("🏁 See my results", type="primary",
                     use_container_width=True, key="wm_finish"):
            st.session_state.wm_phase = "results"
            st.rerun()
    else:
        if st.button("➡ Next number", type="primary",
                     use_container_width=True, key="wm_next"):
            new_span = len(digits) + (1 if ok else 0)
            new_span = min(max(new_span, 3), st.session_state.wm_max_span)
            st.session_state.wm_digits = new_digits(new_span)
            st.session_state.wm_show_index = 0
            st.session_state.wm_show_started_at = time.time()
            st.session_state.wm_typed = ""
            st.session_state.wm_phase = "show"
            st.rerun()
        if st.button("🛑 Stop and see results", use_container_width=True, key="wm_stop"):
            st.session_state.wm_phase = "results"
            st.rerun()

# ===== Results =====
elif phase == "results":
    total = max(st.session_state.wm_total_trials, 1)
    correct = st.session_state.wm_correct_trials
    accuracy = correct / total
    elapsed = time.time() - (st.session_state.wm_start_time or time.time())
    stars = db.calculate_stars_for_accuracy(accuracy)
    star_icons = "⭐" * stars

    st.markdown(
        f"""
        <div class="encouragement">
            🎉 Great work, {user_name}! You earned {star_icons} ({stars} stars).
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mode", st.session_state.wm_mode.capitalize())
    c2.metric("Correct trials", f"{correct} / {total}")
    c3.metric("Accuracy", f"{accuracy*100:.0f}%")
    c4.metric("Best span", st.session_state.wm_max_span_reached)

    db.record_working_memory_result(
        user_id=user_id,
        mode=st.session_state.wm_mode,
        span_length=st.session_state.wm_max_span_reached,
        total_trials=total,
        correct_trials=correct,
        accuracy=accuracy,
        time_spent_seconds=elapsed,
        max_span_reached=st.session_state.wm_max_span_reached,
    )
    db.record_session(
        user_id=user_id,
        module_name="working_memory",
        accuracy=accuracy,
        time_spent_seconds=elapsed,
        score=correct,
        max_score=total,
    )
    db.award_stars(
        user_id=user_id,
        module_name="working_memory",
        stars=stars,
        reason=f"Number memory ({st.session_state.wm_mode}) - {accuracy*100:.0f}%",
    )

    st.markdown("---")
    n1, n2, n3 = st.columns(3)
    with n1:
        if st.button("🔄 Play again", type="primary", use_container_width=True, key="wm_again"):
            reset_state()
            st.rerun()
    with n2:
        if st.button("⚡ Quick Think", use_container_width=True, key="wm_to_proc"):
            reset_state()
            st.switch_page("pages/8_Processing_Speed.py")
    with n3:
        if st.button("🏠 Home", use_container_width=True, key="wm_to_home"):
            reset_state()
            st.switch_page("app.py")

# Teacher mode summary
if not is_child_mode:
    st.divider()
    st.markdown("### 👨‍🏫 Teacher / Parent notes")
    st.write(
        "**Digit-span** is a classic working-memory metric. Forward span tests "
        "short-term storage; backward span additionally taxes the central executive."
    )
    history = db.get_working_memory_history(user_id, limit=10)
    if history:
        st.markdown("Recent sessions:")
        for h in history:
            acc = h.get("accuracy") or 0
            st.write(
                f"- {h.get('created_at','')[:16]} — {h.get('mode','?')} • "
                f"max span {h.get('max_span_reached','?')} • {acc*100:.0f}%"
            )
