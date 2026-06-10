"""
Final Assessment — Comprehensive Evaluation (Fully Implemented)

Walks the child through 6 short mini-tasks (one per cognitive sub-skill) and
produces an overall cognitive profile.

Domains assessed:
  1. Attention            — find target letter inside distractors
  2. Visual memory        — recall letters at highlighted squares in a 3×3 grid (one memorisation, several questions)
  3. Auditory memory      — recall length-N tone sequence (phonological-loop trial)
  4. Word memory          — recall length-N spoken-word sequence (NEW)
  5. Working memory       — backwards digit span trial
  6. Processing speed     — quick same/different + Stroop trials

Scores per domain are 0-100. The DB schema has a single
``auditory_memory_score`` field, so the auditory-memory and word-memory
sub-scores are averaged into it (their individual values are still shown
in the per-skill UI).

Results are persisted via DatabaseHandler.record_final_assessment.
"""

import os
import sys
import time
import random
import string

import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import SessionManager
from utils.theme import apply_theme, render_theme_toggle
from utils.audio import (
    queue_tone,
    queue_sequence,
    play_sequence_now,
    render_audio_queue,
    sequence_total_ms,
    queue_speech,
    speak_sequence_now,
    render_speech_queue,
)
from database.db_handler import DatabaseHandler

SessionManager.initialize_session()
SessionManager.track_page_visit("final_assessment")

st.set_page_config(page_title="Final Test", page_icon="🏆", layout="wide")
apply_theme()
render_audio_queue()    # play any tone queued by the previous click
render_speech_queue()   # speak any word queued by the previous click


# ---------------------------------------------------------------------------
# Page-local CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
.fa-title { font-size: 2.5rem; text-align: center; margin: 0.4rem 0 1rem 0; }
.fa-stage {
    background: var(--app-panel);
    border: 3px solid var(--app-border);
    border-radius: 24px;
    padding: 2rem 1rem;
    text-align: center;
    box-shadow: var(--app-shadow);
}
.fa-pill {
    display: inline-block;
    padding: 0.4rem 1rem;
    border-radius: 999px;
    background: var(--app-panel-alt);
    border: 1px solid var(--app-border);
    font-weight: 600;
}
.fa-progress { display: flex; gap: 0.4rem; justify-content: center; margin-top: 0.6rem; }
.fa-progress-step {
    width: 30px; height: 8px; border-radius: 4px;
    background: var(--app-border);
}
.fa-progress-step.done   { background: var(--app-success); }
.fa-progress-step.active { background: var(--app-accent); }
.fa-big-letter {
    font-size: 5rem; font-weight: 800; letter-spacing: 0.18em;
    color: var(--app-accent);
}
.fa-mini-grid {
    display: inline-grid; grid-template-columns: repeat(3, 90px); gap: 12px;
}
.fa-mini-cell {
    background: linear-gradient(135deg, #42A5F5, #1E88E5);
    color: white; font-size: 2.4rem; font-weight: 800;
    border-radius: 14px; min-height: 90px;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.fa-quiz-recall-grid {
    display: inline-grid;
    grid-template-columns: repeat(3, 90px);
    gap: 12px;
    margin: 0.75rem auto 0 auto;
}
.fa-mini-cell-empty {
    background: #f5f5f5;
    border: 2px solid #cfd8dc;
    border-radius: 14px;
    min-height: 90px;
    box-sizing: border-box;
}
.fa-mini-cell-target {
    background: #fff8f8;
    border: 4px solid #e53935;
    border-radius: 14px;
    min-height: 90px;
    box-sizing: border-box;
    box-shadow:
        0 0 0 4px rgba(229, 57, 53, 0.2),
        inset 0 0 0 2px rgba(229, 57, 53, 0.12);
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOMAINS = [
    "attention",
    "visual_memory",
    "auditory_memory",
    "auditory_words",     # NEW — spoken-word memory
    "working_memory",
    "processing_speed",
]
DOMAIN_LABELS = {
    "attention":         "🎯 Attention",
    "visual_memory":     "🧩 Visual Memory",
    "auditory_memory":   "🔊 Auditory Memory",
    "auditory_words":    "📢 Word Memory",
    "working_memory":    "🔢 Working Memory",
    "processing_speed":  "⚡ Processing Speed",
}
SAFE_LETTERS = "ACEFGHKLMRSTUVX"

# Final Assessment — visual memory: one grid display, then this many questions,
# each about a different cell (no repeats within the assessment).
VM_GRID_SIZE = 3
VM_N_QUESTIONS = 6
VM_MEMORISE_SECONDS = 8.0

AUDIO_PADS = [
    {"id": 0, "label": "🔵", "name": "Blue",   "color": "#1E88E5", "freq": 329.63},
    {"id": 1, "label": "🟢", "name": "Green",  "color": "#43A047", "freq": 261.63},
    {"id": 2, "label": "🟡", "name": "Yellow", "color": "#FDD835", "freq": 392.00},
    {"id": 3, "label": "🔴", "name": "Red",    "color": "#E53935", "freq": 220.00},
]
AUDIO_SEQ_LEN = 5         # phonological-loop trial length (Easy=3 / Hard=7 → middle here)
AUDIO_TONE_MS = 500
AUDIO_GAP_MS  = 220

# Spoken-word memory uses the same dyslexia-friendly word library as the
# standalone module so the assessment matches what the child has practised.
WORD_PADS = [
    {"id": 0, "text": "cat",   "emoji": "🐱", "color": "#FF8A65"},
    {"id": 1, "text": "dog",   "emoji": "🐶", "color": "#A1887F"},
    {"id": 2, "text": "ball",  "emoji": "⚽", "color": "#90A4AE"},
    {"id": 3, "text": "sun",   "emoji": "☀️", "color": "#FFB74D"},
    {"id": 4, "text": "book",  "emoji": "📚", "color": "#4FC3F7"},
    {"id": 5, "text": "tree",  "emoji": "🌳", "color": "#81C784"},
    {"id": 6, "text": "fish",  "emoji": "🐟", "color": "#4DD0E1"},
    {"id": 7, "text": "apple", "emoji": "🍎", "color": "#E57373"},
]
WORD_SEQ_LEN = 4          # one between Easy(3) and Hard(7), keeps the test short

COLOR_NAMES = {
    "RED":   "#E53935",
    "BLUE":  "#1E88E5",
    "GREEN": "#43A047",
    "YELLOW": "#FBC02D",
    "PURPLE": "#8E24AA",
}


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def init_state():
    ss = st.session_state
    ss.setdefault("fa_phase", "intro")              # intro | running | results
    ss.setdefault("fa_step", 0)                     # 0..len(DOMAINS)
    ss.setdefault("fa_substep", "load")             # internal per-domain state
    ss.setdefault("fa_payload", {})                 # data for current domain
    ss.setdefault("fa_scores", {d: None for d in DOMAINS})
    ss.setdefault("fa_start_time", None)            # whole-assessment start (epoch)
    ss.setdefault("fa_step_start", None)            # current-step start (epoch)
    ss.setdefault("fa_step_durations", {})          # domain -> seconds elapsed


def reset_state():
    for k in [
        "fa_phase", "fa_step", "fa_substep", "fa_payload",
        "fa_scores", "fa_start_time", "fa_step_start", "fa_step_durations",
    ]:
        st.session_state.pop(k, None)
    init_state()


def fmt_duration(seconds: float) -> str:
    """Format an upward-counting duration nicely: '45 sec' / '1 min 23 sec'."""
    if seconds is None or seconds < 0:
        return "—"
    total = int(round(seconds))
    m, s = divmod(total, 60)
    if m == 0:
        return f"{s} sec"
    return f"{m} min {s:02d} sec"


init_state()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

db = DatabaseHandler()
user_id = SessionManager.get_user_id()
user_name = SessionManager.get_user_name() or "Friend"
user_age = SessionManager.get_user_age() or 8
is_child_mode = st.session_state.get("app_mode", "child") == "child"

with st.sidebar:
    st.markdown(f"### 👋 Hi, {user_name}!")
    st.markdown(f"### ⭐ Stars: {db.get_total_stars(user_id)}")
    st.divider()
    render_theme_toggle(location="sidebar", key_suffix="fa")
    st.divider()
    if st.button("🏠 Go Home", use_container_width=True, key="fa_home"):
        reset_state()
        st.switch_page("app.py")
    if st.button("🎮 All Games", use_container_width=True, key="fa_all"):
        reset_state()
        st.switch_page("pages/3_Learning_Support.py")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def progress_bar_html(current: int) -> str:
    parts = []
    for i in range(len(DOMAINS)):
        cls = "fa-progress-step"
        if i < current:
            cls += " done"
        elif i == current:
            cls += " active"
        parts.append(f'<div class="{cls}"></div>')
    return f'<div class="fa-progress">{"".join(parts)}</div>'


def play_audio_sequence(sequence):
    """Play tones inline (autoplay) for the given pad-id sequence."""
    freqs = [AUDIO_PADS[i]["freq"] for i in sequence]
    play_sequence_now(freqs, tone_ms=AUDIO_TONE_MS, gap_ms=AUDIO_GAP_MS)


def speak_word_sequence(sequence):
    """Speak the words pointed to by ``sequence`` (indices into WORD_PADS)."""
    speak_sequence_now([WORD_PADS[i]["text"] for i in sequence])


def render_tone_pads_with_flash(sequence: list, tone_ms: int, gap_ms: int,
                                nonce: int) -> None:
    """Render the 4 colored pads inside an iframe and flash them in sync
    with the audio sequence (which plays in the main DOM via
    ``play_audio_sequence``). The same approach used in the standalone
    Auditory Memory page — it makes the section feel like an actual game.

    ``nonce`` makes the iframe re-render on every replay so the flash
    animation re-triggers each time the user clicks "Play again".
    """
    pads_js = ",".join(
        f"{{id:{p['id']}, color:'{p['color']}', label:'{p['label']}', name:'{p['name']}'}}"
        for p in AUDIO_PADS
    )
    seq_js = ",".join(str(s) for s in sequence)
    html = f"""
    <div data-nonce="{nonce}"
         id="fa-aud-pads"
         style="display:grid; grid-template-columns:repeat({len(AUDIO_PADS)}, 1fr);
                gap:14px; justify-content:center; margin-top:0.4rem;">
    </div>
    <script>
      (function() {{
        const pads = [{pads_js}];
        const seq  = [{seq_js}];
        const tone_ms = {tone_ms};
        const gap_ms  = {gap_ms};
        const padArea = document.getElementById('fa-aud-pads');
        if (!padArea) return;
        padArea.innerHTML = '';
        pads.forEach(p => {{
          const el = document.createElement('div');
          el.id = 'fa-pad-' + p.id;
          el.style.cssText = `
              height:120px; border-radius:18px;
              background:${{p.color}}; opacity:0.55;
              box-shadow:0 6px 18px rgba(0,0,0,0.25);
              transition: opacity 120ms ease, transform 120ms ease;
              display:flex; flex-direction:column;
              align-items:center; justify-content:center;
              color:white; font-weight:700;`;
          el.innerHTML = '<div style="font-size:2.4rem;line-height:1;">' +
                         p.label + '</div>' +
                         '<div style="margin-top:0.2rem;">' + p.name + '</div>';
          padArea.appendChild(el);
        }});
        function flash(idx) {{
          const el = document.getElementById('fa-pad-' + pads[idx].id);
          if (!el) return;
          el.style.opacity = '1';
          el.style.transform = 'scale(1.06)';
          setTimeout(() => {{
            el.style.opacity = '0.55';
            el.style.transform = 'scale(1)';
          }}, tone_ms);
        }}
        const gap = tone_ms + gap_ms;
        seq.forEach((idx, i) => setTimeout(() => flash(idx), 60 + i * gap));
      }})();
    </script>
    """
    components.html(html, height=160, scrolling=False)


def render_word_pads_with_flash(sequence: list, nonce: int) -> None:
    """Light-up word pads driven by per-word SpeechSynthesis events.

    Sync model
    ----------
    The speech iframe (``utils/audio.py``) emits one
    ``SpeechSynthesisUtterance`` per word and broadcasts ``word-start`` /
    ``word-end`` messages on the ``aud-sync`` ``BroadcastChannel`` from
    each utterance's actual onstart/onend events. This iframe lights /
    dims the corresponding tile directly in response, so the highlight
    is sample-accurate regardless of voice timing variance.
    """
    pads_js = ",".join(
        f"{{id:{w['id']}, color:'{w['color']}', emoji:'{w['emoji']}', "
        f"text:'{w['text'].capitalize()}'}}"
        for w in WORD_PADS
    )
    seq_js = ",".join(str(s) for s in sequence)
    html = f"""
    <div data-nonce="{nonce}"
         id="fa-word-pads"
         style="display:grid; grid-template-columns:repeat(4, 1fr);
                gap:10px; justify-content:center; margin-top:0.4rem;">
    </div>
    <script>
      (function() {{
        const pads = [{pads_js}];
        const seq  = [{seq_js}];
        const padArea = document.getElementById('fa-word-pads');
        if (!padArea) return;
        padArea.innerHTML = '';
        pads.forEach(w => {{
          const el = document.createElement('div');
          el.id = 'fa-word-' + w.id;
          el.style.cssText = `
              height:100px; border-radius:18px;
              background:${{w.color}}; opacity:0.55;
              box-shadow:0 6px 18px rgba(0,0,0,0.25);
              transition: opacity 220ms cubic-bezier(0.22, 0.61, 0.36, 1),
                          transform 220ms cubic-bezier(0.22, 0.61, 0.36, 1);
              display:flex; flex-direction:column;
              align-items:center; justify-content:center;
              color:white; font-weight:700;`;
          el.innerHTML = '<div style="font-size:2rem;line-height:1;">' +
                         w.emoji + '</div>' +
                         '<div style="margin-top:0.2rem;">' + w.text + '</div>';
          padArea.appendChild(el);
        }});

        function flashOn(padIdx) {{
          const el = document.getElementById('fa-word-' + pads[padIdx].id);
          if (!el) return;
          el.style.opacity = '1';
          el.style.transform = 'scale(1.08)';
        }}
        function flashOff(padIdx) {{
          const el = document.getElementById('fa-word-' + pads[padIdx].id);
          if (!el) return;
          el.style.opacity = '0.55';
          el.style.transform = 'scale(1)';
        }}

        let ch = null;
        try {{ ch = new BroadcastChannel('aud-sync'); }} catch (e) {{}}
        let lastSeen = -1;
        if (ch) {{
          ch.onmessage = function(e) {{
            const d = e.data || {{}};
            if (d.position === undefined || d.position >= seq.length) return;
            if (d.type === 'word-start') {{
              flashOn(seq[d.position]);
              lastSeen = d.position;
            }} else if (d.type === 'word-end') {{
              flashOff(seq[d.position]);
            }}
          }};
        }}

        // Fallback timer chain in case the broadcast is missed.
        const word_ms_est = 700;
        setTimeout(function() {{
          if (lastSeen !== -1) return;
          seq.forEach((padIdx, i) => {{
            setTimeout(() => flashOn(padIdx),  i * word_ms_est);
            setTimeout(() => flashOff(padIdx), i * word_ms_est + (word_ms_est - 100));
          }});
        }}, 1400);
      }})();
    </script>
    """
    components.html(html, height=240, scrolling=False)


def record_score(domain: str, value: float):
    st.session_state.fa_scores[domain] = max(0.0, min(100.0, value))


def advance_step():
    """Record the current step's duration, then move to the next one."""
    ss = st.session_state
    cur_step = ss.fa_step
    if cur_step < len(DOMAINS) and ss.fa_step_start is not None:
        cur_domain = DOMAINS[cur_step]
        ss.fa_step_durations[cur_domain] = time.time() - ss.fa_step_start
    ss.fa_step += 1
    ss.fa_substep = "load"
    ss.fa_payload = {}
    # Next step starts now (None signals "fall through to lazy init below")
    ss.fa_step_start = time.time() if ss.fa_step < len(DOMAINS) else None


def _fa_vm_on_answer(opt_chosen: str, correct: str, cell_pos: int, q_idx: int) -> None:
    """Update visual-memory quiz state when a letter is picked.

    Using ``on_click`` is more reliable than ``if st.button`` + in-body
    mutation + ``st.rerun()``: the callback runs in a defined order and
    avoids the widget/state desync that can leave ``q_index`` stuck.
    """
    pld = st.session_state.fa_payload
    if opt_chosen == correct:
        pld["correct"] = pld.get("correct", 0) + 1
    asked = pld.setdefault("asked", [])
    if cell_pos not in asked:
        asked.append(cell_pos)
    pld["q_index"] = q_idx + 1


_SYSRNG = random.SystemRandom()  # OS-level entropy → strong cross-run variety


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown('<p class="fa-title">🏆 Final Challenge</p>', unsafe_allow_html=True)

phase = st.session_state.fa_phase

# ===== Intro =====
if phase == "intro":
    st.markdown(
        f"""
        <div class="instruction-box">
            <strong>👋 Hi {user_name}!</strong><br><br>
            <strong>🎯 This is your big challenge!</strong> You'll do six short games, one per skill:
            <ol>
                <li>🎯 Attention — find a target letter in a row.</li>
                <li>🧩 Visual memory — remember letters in a small grid.</li>
                <li>🔊 Sound memory — repeat a tune.</li>
                <li>📢 Word memory — repeat a list of spoken words.</li>
                <li>🔢 Number memory — say numbers backwards.</li>
                <li>⚡ Quick think — same or different?</li>
            </ol>
            It takes about 6–8 minutes. Ready?
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns([1, 2, 1])
    with cols[1]:
        if st.button("🚀 Start the Final Challenge", type="primary",
                     use_container_width=True, key="fa_start"):
            reset_state()
            now = time.time()
            st.session_state.fa_phase = "running"
            st.session_state.fa_step = 0
            st.session_state.fa_substep = "load"
            st.session_state.fa_start_time = now
            st.session_state.fa_step_start = now
            st.rerun()

# ===== Running =====
elif phase == "running":
    step = st.session_state.fa_step

    # All sub-tasks done → results
    if step >= len(DOMAINS):
        st.session_state.fa_phase = "results"
        st.rerun()

    # Belt-and-braces: make sure both timers are running. fa_start_time is
    # the whole-assessment clock; fa_step_start is the current sub-task clock.
    now = time.time()
    if st.session_state.fa_start_time is None:
        st.session_state.fa_start_time = now
    if st.session_state.fa_step_start is None:
        st.session_state.fa_step_start = now
    elapsed_total = now - st.session_state.fa_start_time
    elapsed_step  = now - st.session_state.fa_step_start

    current_domain = DOMAINS[step]
    st.markdown(progress_bar_html(step), unsafe_allow_html=True)
    st.markdown(
        f'<div style="text-align:center; margin-top:0.3rem; '
        f'display:flex; flex-wrap:wrap; gap:0.5rem; justify-content:center;">'
        f'<span class="fa-pill">Step {step+1} / {len(DOMAINS)} — {DOMAIN_LABELS[current_domain]}</span>'
        f'<span class="fa-pill">⏱ This step: {fmt_duration(elapsed_step)}</span>'
        f'<span class="fa-pill">🕒 Total: {fmt_duration(elapsed_total)}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ----- Attention task -----
    if current_domain == "attention":
        ss = st.session_state
        if ss.fa_substep == "load":
            target = random.choice(SAFE_LETTERS)
            distractors = [c for c in SAFE_LETTERS if c != target]
            n_total = 12
            n_targets = 4
            row = random.sample(distractors, n_total - n_targets) + [target] * n_targets
            random.shuffle(row)
            ss.fa_payload = {"target": target, "row": row, "picks": []}
            ss.fa_substep = "play"
            st.rerun()

        target = ss.fa_payload["target"]
        row = ss.fa_payload["row"]
        picks = ss.fa_payload["picks"]
        n_targets = sum(1 for c in row if c == target)

        st.markdown(
            f"""
            <div class="fa-stage">
                <p style="font-size:1.2rem; margin-bottom:0.6rem;">Click <strong>every</strong>
                tile that shows the letter:</p>
                <div class="fa-big-letter">{target}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cols = st.columns(len(row))
        for i, ch in enumerate(row):
            with cols[i]:
                already = i in picks
                if st.button(ch, use_container_width=True,
                             key=f"fa_att_{i}",
                             type="primary" if already else "secondary",
                             disabled=already):
                    picks.append(i)
                    ss.fa_payload["picks"] = picks
                    st.rerun()

        if st.button("✅ Done", type="primary", use_container_width=True, key="fa_att_done"):
            correct = sum(1 for i in picks if row[i] == target)
            wrong = sum(1 for i in picks if row[i] != target)
            # Score: % targets caught minus penalty for wrong picks
            base = correct / n_targets if n_targets else 0.0
            penalty = min(0.3, wrong * 0.1)
            score = max(0.0, base - penalty) * 100
            record_score("attention", score)
            advance_step()
            st.rerun()

    # ----- Visual memory -----
    #
    # Like the auditory steps, this branch tracks state on the payload itself
    # (``pld["sub"]``) instead of the shared ``fa_substep`` so consecutive
    # reruns can never reset us back to the show/load phase. The grid is shown
    # once; we then ask ``VM_N_QUESTIONS`` questions about distinct cells only
    # (no duplicate positions in one run). ``pld["asked"]`` records completed
    # cells as a safety net.
    elif current_domain == "visual_memory":
        ss = st.session_state
        pld = ss.fa_payload

        # ---- DEFENSIVE BANNER (always renders) -----------------------------
        st.markdown(
            f"""
            <div class="fa-stage" style="background: linear-gradient(135deg,#2E7D32,#66BB6A);
                                          color: white; border: 0;">
                <div style="font-size:3rem; line-height:1;">🧩</div>
                <div style="font-size:1.6rem; font-weight:800; margin-top:0.3rem;">
                    Step {step+1} of {len(DOMAINS)} — Visual Memory
                </div>
                <div style="opacity:0.95; margin-top:0.3rem;">
                    Watch the 3×3 grid of letters once, then answer {VM_N_QUESTIONS}
                    questions — each shows an empty grid with one square ringed; pick the letter that was there.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- Lazy init in same pass --------------------------------------
        if "grid" not in pld:
            pld["grid"] = _SYSRNG.sample(SAFE_LETTERS, 9)
            pld["show_until"] = time.time() + VM_MEMORISE_SECONDS
            pld["asked"] = []
            pld["correct"] = 0
            pld["sub"] = "show"
            pld["vm_option_orders"] = {}

        grid     = pld["grid"]
        sub      = pld.get("sub", "show")
        n_quiz = VM_N_QUESTIONS

        if sub == "show":
            remaining = pld["show_until"] - time.time()
            if remaining <= 0:
                # Done memorising — ``n_quiz`` distinct cells (no duplicates).
                n_cells = VM_GRID_SIZE * VM_GRID_SIZE
                k = min(n_quiz, n_cells)
                pld["positions"] = _SYSRNG.sample(range(n_cells), k)
                pld["q_index"] = 0
                pld["sub"] = "quiz"
                st.rerun()
            cells_html = "".join(f'<div class="fa-mini-cell">{c}</div>' for c in grid)
            st.markdown(
                f"""
                <div style="text-align:center; margin-top:0.4rem;">
                    <p style="font-size:1.2rem;">👀 Memorise the grid! Time left:
                    <strong>{int(remaining)+1}s</strong></p>
                    <div style="display:flex; justify-content:center; margin-top:0.6rem;">
                        <div class="fa-mini-grid">{cells_html}</div>
                    </div>
        </div>
                """,
                unsafe_allow_html=True,
            )
            # ~1 Hz refresh: avoids dozens of full-app reruns per second (was
            # sleep(0.3)), which felt laggy and could interfere with clicks.
            time.sleep(min(1.0, max(0.15, remaining)))
            st.rerun()

        elif sub == "quiz":
            qi        = pld["q_index"]
            positions = pld["positions"]

            if qi >= len(positions):
                score = (pld["correct"] / len(positions)) * 100
                record_score("visual_memory", score)
                advance_step()
                st.rerun()

            # Belt-and-braces: never ask the same cell twice in a single
            # visit. If somehow the next position is already in pld["asked"],
            # pick a fresh distributed cell.
            pos = positions[qi]
            if pos in pld["asked"]:
                avail = [
                    c for c in range(VM_GRID_SIZE * VM_GRID_SIZE)
                    if c not in pld["asked"]
                ]
                if avail:
                    pos = _SYSRNG.choice(avail)
                    positions[qi] = pos
                    pld.get("vm_option_orders", {}).pop(qi, None)

            correct_letter = grid[pos]
            orders = pld.setdefault("vm_option_orders", {})
            if qi not in orders:
                wrongs = _SYSRNG.sample(
                    [c for c in SAFE_LETTERS if c != correct_letter], 3
                )
                opts = wrongs + [correct_letter]
                _SYSRNG.shuffle(opts)
                orders[qi] = opts
            options = list(orders[qi])

            n_cells = VM_GRID_SIZE * VM_GRID_SIZE
            cells_quiz = "".join(
                f'<div class="{"fa-mini-cell-target" if i == pos else "fa-mini-cell-empty"}"></div>'
                for i in range(n_cells)
            )
            st.markdown(
                f"""
                <div style="text-align:center; margin-top:0.6rem;">
                    <p style="font-size:1.3rem;">Question {qi+1} of {n_quiz}:
                    What letter was in the <strong>highlighted</strong> square?</p>
                    <div style="display:flex; justify-content:center;">
                        <div class="fa-quiz-recall-grid">{cells_quiz}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            cols = st.columns(len(options))
            for i, opt in enumerate(options):
                with cols[i]:
                    btn_key = f"fa_s{step}_vm_q{qi}_cell{pos}_i{i}"
                    st.button(
                        opt,
                        use_container_width=True,
                        key=btn_key,
                        on_click=_fa_vm_on_answer,
                        args=(opt, correct_letter, pos, qi),
                    )

    # ----- Auditory memory (phonological-loop tone trial) -----
    #
    # The branch is split into THREE fully-independent rendering blocks so
    # that even if any earlier step had a half-state issue, the section
    # banner ALWAYS renders. The substep is stored on the payload itself
    # (``pld["sub"]``) — not on ``ss.fa_substep`` which is reset to "load"
    # by ``advance_step`` and could collide with code from previous steps.
    elif current_domain == "auditory_memory":
        ss = st.session_state
        pld = ss.fa_payload

        # ---- DEFENSIVE BANNER (always renders, regardless of payload) ----
        st.markdown(
            f"""
            <div class="fa-stage" style="background: linear-gradient(135deg,#1565C0,#42A5F5);
                                          color: white; border: 0;">
                <div style="font-size:3rem; line-height:1;">🔊</div>
                <div style="font-size:1.6rem; font-weight:800; margin-top:0.3rem;">
                    Step {step+1} of {len(DOMAINS)} — Sound Memory
                </div>
                <div style="opacity:0.95; margin-top:0.3rem;">
                    Listen to the {AUDIO_SEQ_LEN}-tone sequence, then tap the pads
                    in the same order.
                </div>
        </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- Lazy init in the SAME pass we render the listen UI ----
        if not pld.get("sequence"):
            seq = []
            while len(seq) < AUDIO_SEQ_LEN:
                idx = random.randint(0, len(AUDIO_PADS) - 1)
                if not seq or seq[-1] != idx:
                    seq.append(idx)
            pld["sequence"] = seq
            pld["typed"] = []
            pld["played_count"] = 1
            pld["sub"] = "listen"
            # Auto-play once on entry — we're in the same pass as the click
            # that landed us here, so the autoplay tag gets the user gesture.
            play_audio_sequence(seq)

        seq = pld["sequence"]
        sub = pld.get("sub", "listen")

        if sub == "listen":
            # Render the 4 pads inside an iframe and flash them in sync with
            # the audio. ``played_count`` is the nonce — every replay
            # increments it, so the iframe re-mounts and the flash animation
            # re-runs from the start.
            render_tone_pads_with_flash(
                seq, AUDIO_TONE_MS, AUDIO_GAP_MS,
                nonce=pld.get("played_count", 1),
            )

            cols = st.columns([1, 1, 1])
            with cols[0]:
                if st.button("🔁 Play again", use_container_width=True, key="fa_aud_play"):
                    queue_sequence(
                        [AUDIO_PADS[i]["freq"] for i in seq],
                        tone_ms=AUDIO_TONE_MS, gap_ms=AUDIO_GAP_MS,
                    )
                    pld["played_count"] = pld.get("played_count", 0) + 1
                    st.rerun()
            with cols[1]:
                total_s = sequence_total_ms(len(seq), AUDIO_TONE_MS, AUDIO_GAP_MS) / 1000
                st.markdown(
                    f'<div style="text-align:center; padding-top:0.4rem; color:var(--app-muted);">'
                    f'~{total_s:.1f}s • played {pld["played_count"]}×</div>',
                    unsafe_allow_html=True,
                )
            with cols[2]:
                if st.button("👉 I'm ready, repeat the sequence",
                             type="primary", use_container_width=True,
                             key="fa_aud_ready"):
                    pld["sub"] = "tap"
                    st.rerun()

        elif sub == "tap":
            typed = pld["typed"]
            progress = "".join("🟩 " if i < len(typed) else "⬜ " for i in range(len(seq)))
            st.markdown(
                f'<div class="fa-stage"><p style="font-size:1.5rem;">{progress}</p></div>',
                unsafe_allow_html=True,
            )
            cols = st.columns(len(AUDIO_PADS))
            for i, p in enumerate(AUDIO_PADS):
                with cols[i]:
                    st.markdown(
                        f'<div style="background:{p["color"]}; height:110px; '
                        f'border-radius:18px; display:flex; flex-direction:column; '
                        f'align-items:center; justify-content:center; color:white; '
                        f'font-weight:700;">'
                        f'<div style="font-size:2.4rem;line-height:1;">{p["label"]}</div>'
                        f'<div style="margin-top:0.2rem;">{p["name"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button(f"Tap {p['name']}", use_container_width=True,
                                 key=f"fa_aud_pad_{i}_{len(typed)}"):
                        queue_tone(p["freq"], duration_ms=380)
                        typed.append(i)
                        pld["typed"] = typed
                        if len(typed) == len(seq):
                            n_correct = sum(1 for a, b in zip(typed, seq) if a == b)
                            score = (n_correct / len(seq)) * 100
                            record_score("auditory_memory", score)
                            advance_step()
                        st.rerun()

            tcols = st.columns(2)
            with tcols[0]:
                if st.button("↩ Reset taps", key="fa_aud_reset",
                             use_container_width=True):
                    pld["typed"] = []
                    st.rerun()
            with tcols[1]:
                if st.button("🔁 Hear it again", key="fa_aud_replay_in_tap",
                             use_container_width=True):
                    freqs = [AUDIO_PADS[idx]["freq"] for idx in seq]
                    queue_sequence(freqs, tone_ms=AUDIO_TONE_MS, gap_ms=AUDIO_GAP_MS)
                    st.rerun()

    # ----- Word memory (NEW spoken-word phonological-loop trial) -----
    #
    # Same defensive-banner + same-pass-init pattern as auditory_memory.
    elif current_domain == "auditory_words":
        ss = st.session_state
        pld = ss.fa_payload

        st.markdown(
            f"""
            <div class="fa-stage" style="background: linear-gradient(135deg,#6A1B9A,#AB47BC);
                                          color: white; border: 0;">
                <div style="font-size:3rem; line-height:1;">📢</div>
                <div style="font-size:1.6rem; font-weight:800; margin-top:0.3rem;">
                    Step {step+1} of {len(DOMAINS)} — Word Memory
                </div>
                <div style="opacity:0.95; margin-top:0.3rem;">
                    Listen to the {WORD_SEQ_LEN} spoken words, then tap them in the same order.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not pld.get("sequence"):
            seq = []
            while len(seq) < WORD_SEQ_LEN:
                idx = random.randint(0, len(WORD_PADS) - 1)
                if not seq or seq[-1] != idx:
                    seq.append(idx)
            pld["sequence"] = seq
            pld["typed"] = []
            pld["played_count"] = 1
            pld["sub"] = "listen"
            speak_word_sequence(seq)

        seq = pld["sequence"]
        sub = pld.get("sub", "listen")

        if sub == "listen":
            st.markdown(
                """
                <div style="text-align:center; padding:0.6rem 0;">
                    <div style="font-size:2.4rem;">👂</div>
                    <div style="color:var(--app-muted); margin-top:0.2rem;">
                        The words are read aloud — they aren't shown on screen.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Render the word pads in an iframe and flash the ones in the
            # sequence as they are spoken (same UX as the colored pads).
            render_word_pads_with_flash(
                seq, nonce=pld.get("played_count", 1),
            )

            cols = st.columns([1, 1, 1])
            with cols[0]:
                if st.button("🔁 Play again", use_container_width=True, key="fa_words_play"):
                    queue_speech([WORD_PADS[i]["text"] for i in seq])
                    pld["played_count"] = pld.get("played_count", 0) + 1
                    st.rerun()
            with cols[1]:
                approx_s = max(2.0, len(seq) * 0.8)
                st.markdown(
                    f'<div style="text-align:center; padding-top:0.4rem; color:var(--app-muted);">'
                    f'~{approx_s:.1f}s • played {pld["played_count"]}×</div>',
                    unsafe_allow_html=True,
                )
            with cols[2]:
                if st.button("👉 I'm ready, repeat the words",
                             type="primary", use_container_width=True,
                             key="fa_words_ready"):
                    pld["sub"] = "tap"
                    st.rerun()

        elif sub == "tap":
            typed = pld["typed"]
            progress = "".join("🟩 " if i < len(typed) else "⬜ " for i in range(len(seq)))
            st.markdown(
                f'<div class="fa-stage"><p style="font-size:1.5rem;">{progress}</p></div>',
                unsafe_allow_html=True,
            )
            ROW_LEN = 4
            for row_start in range(0, len(WORD_PADS), ROW_LEN):
                row_items = WORD_PADS[row_start: row_start + ROW_LEN]
                row_cols = st.columns(ROW_LEN)
                for j, w in enumerate(row_items):
                    with row_cols[j]:
                        st.markdown(
                            f'<div style="background:{w["color"]}; height:110px; '
                            f'border-radius:18px; display:flex; flex-direction:column; '
                            f'align-items:center; justify-content:center; color:white; '
                            f'font-weight:700;">'
                            f'<div style="font-size:2.4rem;line-height:1;">{w["emoji"]}</div>'
                            f'<div style="margin-top:0.2rem;">{w["text"].capitalize()}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        if st.button(
                            f"Tap {w['text'].capitalize()}",
                            use_container_width=True,
                            key=f"fa_words_pad_{w['id']}_{len(typed)}",
                        ):
                            queue_speech(w["text"])
                            typed.append(w["id"])
                            pld["typed"] = typed
                            if len(typed) == len(seq):
                                n_correct = sum(
                                    1 for a, b in zip(typed, seq) if a == b
                                )
                                score = (n_correct / len(seq)) * 100
                                record_score("auditory_words", score)
                                advance_step()
                            st.rerun()

            tcols = st.columns(2)
            with tcols[0]:
                if st.button("↩ Reset taps", key="fa_words_reset",
                             use_container_width=True):
                    pld["typed"] = []
                    st.rerun()
            with tcols[1]:
                if st.button("🔁 Hear it again", key="fa_words_replay_in_tap",
                             use_container_width=True):
                    queue_speech([WORD_PADS[idx]["text"] for idx in seq])
                    st.rerun()

    # ----- Working memory (backward digit span 4) -----
    elif current_domain == "working_memory":
        ss = st.session_state
        if ss.fa_substep == "load":
            digits = []
            while len(digits) < 4:
                d = random.randint(0, 9)
                if not digits or digits[-1] != d:
                    digits.append(d)
            ss.fa_payload = {
                "digits": digits,
                "show_until": time.time() + 4.0,
                "typed": "",
            }
            ss.fa_substep = "show"
            st.rerun()

        digits = ss.fa_payload["digits"]

        if ss.fa_substep == "show":
            elapsed = time.time() - (ss.fa_payload["show_until"] - 4.0)
            per = 1.0
            idx = int(elapsed // per)
            if elapsed >= 4.0:
                ss.fa_substep = "type"
                st.rerun()
            else:
                d = digits[min(idx, len(digits) - 1)]
                st.markdown(
                    f"""
                    <div class="fa-stage">
                        <p style="font-size:1.2rem;">👀 Watch the numbers, then type them
                        <strong>backwards</strong>.</p>
                        <div class="fa-big-letter" style="font-size:6rem;">{d}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                time.sleep(0.25)
                st.rerun()

        elif ss.fa_substep == "type":
            typed = ss.fa_payload["typed"]
            st.markdown(
                f"""
                <div class="fa-stage">
                    <p style="font-size:1.2rem;">Type the digits <strong>in reverse order</strong>.</p>
                    <div class="fa-big-letter">{typed if typed else "&nbsp;"}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            keypad = [["1","2","3"],["4","5","6"],["7","8","9"],["⌫","0","✓"]]
            for row in keypad:
                cols = st.columns(3)
                for c, label in zip(cols, row):
                    with c:
                        if st.button(label, use_container_width=True,
                                     key=f"fa_wm_{label}_{len(typed)}"):
                            if label == "⌫":
                                ss.fa_payload["typed"] = typed[:-1]
                                st.rerun()
                            elif label == "✓":
                                expected = "".join(str(x) for x in reversed(digits))
                                n_correct = sum(
                                    1 for a, b in zip(typed.ljust(len(expected)), expected) if a == b
                                )
                                score = (n_correct / len(expected)) * 100 if typed else 0
                                # Bonus if exactly correct
                                if typed == expected:
                                    score = 100.0
                                record_score("working_memory", score)
                                advance_step()
                                st.rerun()
                            else:
                                if len(typed) < len(digits):
                                    ss.fa_payload["typed"] = typed + label
                                    st.rerun()

    # ----- Processing speed (3 quick mixed trials) -----
    elif current_domain == "processing_speed":
        ss = st.session_state
        if ss.fa_substep == "load":
            ss.fa_payload = {
                "n_trials": 3, "i": 0, "correct": 0,
                "rts": [], "current": None, "started": None,
            }
            ss.fa_substep = "next_trial"
            st.rerun()

        if ss.fa_substep == "next_trial":
            if ss.fa_payload["i"] >= ss.fa_payload["n_trials"]:
                acc = ss.fa_payload["correct"] / ss.fa_payload["n_trials"]
                avg_rt = (
                    sum(ss.fa_payload["rts"]) / len(ss.fa_payload["rts"])
                    if ss.fa_payload["rts"] else 5000.0
                )
                # Score = accuracy(70%) + speed(30%) where speed maps 0..3000ms -> 100..0
                speed_pts = max(0.0, min(1.0, (3000 - avg_rt) / 3000)) * 100
                score = acc * 70 + speed_pts * 0.3
                record_score("processing_speed", score)
                advance_step()
                st.rerun()
            kind = random.choice(["same_diff", "color_match"])
            if kind == "same_diff":
                same = random.random() < 0.5
                a = random.choice(string.ascii_lowercase)
                b = a if same else random.choice([x for x in string.ascii_lowercase if x != a])
                ss.fa_payload["current"] = {
                    "kind": "same_diff",
                    "letters": (a, b),
                    "answer": "same" if same else "different",
                }
            else:
                word = random.choice(list(COLOR_NAMES.keys()))
                ink = random.choice([c for c in COLOR_NAMES if c != word])
                ss.fa_payload["current"] = {
                    "kind": "color_match",
                    "word": word,
                    "ink": ink,
                    "answer": ink,
                }
            ss.fa_payload["started"] = time.time()
            ss.fa_substep = "trial"
            st.rerun()

        elif ss.fa_substep == "trial":
            trial = ss.fa_payload["current"]
            elapsed = time.time() - ss.fa_payload["started"]
            remaining = max(0.0, 5.0 - elapsed)

            st.markdown(
                f'<div style="text-align:center; margin-bottom:0.4rem;">'
                f'<span class="fa-pill">Quick! ⏳ {remaining:0.1f}s • '
                f'Trial {ss.fa_payload["i"]+1}/{ss.fa_payload["n_trials"]}</span></div>',
                unsafe_allow_html=True,
            )

            def grade(answer):
                rt_ms = (time.time() - ss.fa_payload["started"]) * 1000
                if answer == trial["answer"]:
                    ss.fa_payload["correct"] += 1
                ss.fa_payload["rts"].append(rt_ms)
                ss.fa_payload["i"] += 1
                ss.fa_substep = "next_trial"

            if remaining <= 0:
                ss.fa_payload["rts"].append(5000.0)
                ss.fa_payload["i"] += 1
                ss.fa_substep = "next_trial"
                st.rerun()

            if trial["kind"] == "same_diff":
                a, b = trial["letters"]
                st.markdown(
                    f"""
                    <div class="fa-stage">
                        <div style="font-size:5rem; font-weight:800; letter-spacing:0.4em;
                                    color:var(--app-accent);">{a}&nbsp;&nbsp;{b}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Same", type="primary", use_container_width=True,
                                 key=f"fa_ps_same_{ss.fa_payload['i']}"):
                        grade("same"); st.rerun()
                with c2:
                    if st.button("❌ Different", type="primary", use_container_width=True,
                                 key=f"fa_ps_diff_{ss.fa_payload['i']}"):
                        grade("different"); st.rerun()
            else:
                ink_color = COLOR_NAMES[trial["ink"]]
                st.markdown(
                    f"""
                    <div class="fa-stage">
                        <div style="font-size:4rem; font-weight:800; color:{ink_color};">
                            {trial['word']}
                        </div>
                        <p style="margin-top:0.6rem;">Click the colour the word is <em>painted in</em>.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                names = list(COLOR_NAMES.keys())
                random.Random(trial["word"] + trial["ink"]).shuffle(names)
                cols = st.columns(len(names))
                for c, name in zip(cols, names):
                    with c:
                        if st.button(name, use_container_width=True,
                                     key=f"fa_ps_col_{name}_{ss.fa_payload['i']}"):
                            grade(name); st.rerun()

            time.sleep(0.2)
            st.rerun()

# ===== Results =====
elif phase == "results":
    scores    = st.session_state.fa_scores
    durations = st.session_state.fa_step_durations or {}
    elapsed   = time.time() - (st.session_state.fa_start_time or time.time())
    # Total = sum of recorded per-step durations, with overall-elapsed as a
    # belt-and-braces fallback if any step duration didn't get recorded.
    sum_steps = sum(durations.values())
    total_time = sum_steps if sum_steps > 0 else elapsed
    valid = [v for v in scores.values() if v is not None]
    overall = sum(valid) / len(valid) if valid else 0.0

    # 0-100 -> stars
    if overall >= 85:
        stars = 5
    elif overall >= 70:
        stars = 4
    elif overall >= 55:
        stars = 3
    elif overall >= 40:
        stars = 2
    else:
        stars = 1
    star_icons = "⭐" * stars

    # Build a friendly summary
    strengths = sorted(scores.items(), key=lambda kv: -(kv[1] or 0))[:2]
    weakest = sorted(scores.items(), key=lambda kv: (kv[1] or 0))[:1]
    summary_lines = [
        f"Overall score: {overall:.1f}/100",
        f"Strongest: {', '.join(DOMAIN_LABELS[d] for d, _ in strengths)}",
        f"Most room to grow: {DOMAIN_LABELS[weakest[0][0]]}" if weakest else "",
    ]
    summary = " | ".join([s for s in summary_lines if s])

    st.markdown(
        f"""
        <div class="encouragement">
            🏆 You did it, {user_name}! {star_icons} ({stars} stars)<br>
            Overall score: <strong>{overall:.0f}/100</strong> &nbsp;•&nbsp;
            Total time: <strong>{fmt_duration(total_time)}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 6 domains is too many cards on one row → use 3 + 3 layout.
    half = (len(DOMAINS) + 1) // 2
    for row_start in (0, half):
        row_domains = DOMAINS[row_start: row_start + half]
        row_cols = st.columns(len(row_domains))
        for col, dom in zip(row_cols, row_domains):
            with col:
                v = scores.get(dom)
                st.metric(DOMAIN_LABELS[dom], f"{v:.0f}" if v is not None else "—")
                if v is not None:
                    st.progress(min(1.0, v / 100.0))

    # ---- Per-exercise timing breakdown -------------------------------------
    # NOTE: build the HTML on a SINGLE line (no leading whitespace) — if any
    # row starts with 4+ spaces, Streamlit's markdown parser treats it as a
    # code block and prints raw <tr>/<td> tags instead of rendering them.
    st.markdown("### ⏱ Time taken")
    rows_html = []
    td_l = '<td style="padding:0.45rem 0.8rem;">'
    td_r = '<td style="padding:0.45rem 0.8rem; text-align:right; font-weight:700;">'
    for dom in DOMAINS:
        dur = durations.get(dom)
        dur_text = fmt_duration(dur) if dur is not None else "—"
        rows_html.append(
            f"<tr>{td_l}{DOMAIN_LABELS[dom]}</td>"
            f"{td_r}{dur_text}</td></tr>"
        )
    total_td_l = '<td style="padding:0.6rem 0.8rem; font-weight:800;">'
    total_td_r = (
        '<td style="padding:0.6rem 0.8rem; text-align:right; font-weight:800;'
        ' color: var(--app-accent);">'
    )
    rows_html.append(
        f'<tr style="border-top:2px solid var(--app-border);">'
        f"{total_td_l}🏁 Total</td>"
        f"{total_td_r}{fmt_duration(total_time)}</td></tr>"
    )
    table_html = (
        '<div style="background: var(--app-panel);'
        ' border:1px solid var(--app-border);'
        ' border-radius:14px; padding:0.4rem 0.4rem;'
        ' box-shadow: var(--app-shadow);">'
        '<table style="width:100%; border-collapse:collapse;'
        ' font-size:1.05rem;">'
        + "".join(rows_html)
        + "</table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("### 📝 Summary")
    st.write(summary or "—")

    with st.expander("Per-skill notes"):
        notes = {
            "attention":        "How well the child found target letters quickly without missing or false-clicking.",
            "visual_memory":    "Memory for letters in a 3×3 grid (several questions, each about a different cell).",
            "auditory_memory":  f"Repeating a {AUDIO_SEQ_LEN}-tone sequence (Simon-style).",
            "auditory_words":   f"Repeating a {WORD_SEQ_LEN}-word spoken sequence in the same order.",
            "working_memory":   "Saying back a 4-digit sequence in reverse order.",
            "processing_speed": "Quick same/different and Stroop trials — accuracy and reaction time.",
        }
        for dom, note in notes.items():
            v = scores.get(dom)
            st.write(
                f"- **{DOMAIN_LABELS[dom]} ({v:.0f}/100):** {note}"
                if v is not None
                else f"- **{DOMAIN_LABELS[dom]}:** skipped"
            )

    # The DB has a single ``auditory_memory_score`` slot. We combine the two
    # auditory sub-tasks (tones + spoken words) by averaging the available
    # values so teacher history captures both.
    aud_parts = [v for k, v in scores.items()
                 if k in ("auditory_memory", "auditory_words") and v is not None]
    aud_combined = sum(aud_parts) / len(aud_parts) if aud_parts else 0

    # Embed per-step timings inside the summary string so teachers see the
    # breakdown in DB history without needing a schema migration.
    timing_summary = " · ".join(
        f"{DOMAIN_LABELS[d]}={fmt_duration(durations.get(d))}"
        for d in DOMAINS if d in durations
    )
    full_summary = (summary + (" | Times: " + timing_summary if timing_summary else "") +
                    f" | Total time: {fmt_duration(total_time)}")

    db.record_final_assessment(
        user_id=user_id,
        overall_score=overall,
        attention_score=scores.get("attention") or 0,
        visual_memory_score=scores.get("visual_memory") or 0,
        auditory_memory_score=aud_combined,
        working_memory_score=scores.get("working_memory") or 0,
        processing_speed_score=scores.get("processing_speed") or 0,
        time_spent_seconds=total_time,
        age_at_test=user_age,
        summary=full_summary,
    )
    db.record_session(
        user_id=user_id,
        module_name="final_assessment",
        accuracy=overall / 100.0,
        time_spent_seconds=total_time,
        score=int(overall),
        max_score=100,
    )
    db.award_stars(
        user_id=user_id,
        module_name="final_assessment",
        stars=stars,
        reason=f"Final assessment - {overall:.0f}/100",
    )

    st.markdown("---")
    n1, n2, n3 = st.columns(3)
    with n1:
        if st.button("🔄 Try again", type="primary", use_container_width=True, key="fa_retry"):
            reset_state()
            st.rerun()
    with n2:
        if st.button("🎮 Practice some more", use_container_width=True, key="fa_practice"):
            reset_state()
            st.switch_page("pages/3_Learning_Support.py")
    with n3:
        if st.button("🏠 Home", use_container_width=True, key="fa_home2"):
            reset_state()
            st.switch_page("app.py")

# Teacher view
if not is_child_mode and phase != "intro":
    st.divider()
    st.markdown("### 👨‍🏫 Teacher / Parent notes")
    st.write(
        "The final assessment combines five short tasks into a single profile. "
        "Per-domain scores are 0-100 and the overall score is their mean. "
        "Use the per-skill notes to interpret strengths and weaknesses."
    )
    history = db.get_final_assessment_history(user_id, limit=10)
    if history:
        st.markdown("Recent assessments:")
        for h in history:
            st.write(
                f"- {h.get('created_at','')[:16]} — Overall {h.get('overall_score',0):.0f}/100 "
                f"(att {h.get('attention_score',0):.0f}, vm {h.get('visual_memory_score',0):.0f}, "
                f"am {h.get('auditory_memory_score',0):.0f}, wm {h.get('working_memory_score',0):.0f}, "
                f"ps {h.get('processing_speed_score',0):.0f})"
            )
