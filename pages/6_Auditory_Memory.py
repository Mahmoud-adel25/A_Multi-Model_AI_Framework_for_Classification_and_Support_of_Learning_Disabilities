"""
Auditory Memory Module — Phonological-Loop Trainer

Designed to exercise the phonological loop component of working memory
(commonly weaker in dyslexic learners): the child listens to a sequence of
distinct tones, mentally rehearses them (each pad has a colour name the child
can sub-vocalise), and reproduces the sequence by tapping the matching pads
in the correct order.

Difficulty (sequence length the round starts with):
    Easy   = 3 items
    Medium = 5 items
    Hard   = 7 items

After a correct round the sequence grows by 1 (capped at 10) so the child can
keep stretching their span. Each round is also re-tapped one-tone-at-a-time
with audio feedback per tap, so the child can self-correct.

Audio is generated server-side as WAV bytes and emitted with
``<audio autoplay>`` directly into the page DOM (see ``utils/audio.py``).
This bypasses Streamlit's iframe component, which is why per-tap sounds
now play correctly across reruns.
"""

import os
import sys
import time
import random

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
    speak_now,
    speak_sequence_now,
    render_speech_queue,
)
from database.db_handler import DatabaseHandler

SessionManager.initialize_session()
SessionManager.track_page_visit("auditory_memory")

st.set_page_config(page_title="Sound Memory Game", page_icon="🔊", layout="wide")
apply_theme()
render_audio_queue()    # play any tone queued by the previous click
render_speech_queue()   # speak any word queued by the previous click


# ---------------------------------------------------------------------------
# Configuration — pads carry a colour AND a short word the child can rehearse
# ---------------------------------------------------------------------------

PADS = [
    {"id": 0, "label": "🔵", "name": "Blue",   "color": "#1E88E5", "freq": 329.63},  # E4
    {"id": 1, "label": "🟢", "name": "Green",  "color": "#43A047", "freq": 261.63},  # C4
    {"id": 2, "label": "🟡", "name": "Yellow", "color": "#FDD835", "freq": 392.00},  # G4
    {"id": 3, "label": "🔴", "name": "Red",    "color": "#E53935", "freq": 220.00},  # A3
]

# Dyslexia-friendly short words. Each word has an emoji + a colour so the pad
# is visually distinct, but the *task* is auditory: the system reads them
# aloud and the child reproduces the sequence. Children with dyslexia often
# struggle most with the phonological loop, which is exactly what this
# activity exercises.
WORDS = [
    {"id": 0, "text": "cat",   "emoji": "🐱", "color": "#FF8A65"},
    {"id": 1, "text": "dog",   "emoji": "🐶", "color": "#A1887F"},
    {"id": 2, "text": "ball",  "emoji": "⚽", "color": "#90A4AE"},
    {"id": 3, "text": "sun",   "emoji": "☀️", "color": "#FFB74D"},
    {"id": 4, "text": "book",  "emoji": "📚", "color": "#4FC3F7"},
    {"id": 5, "text": "tree",  "emoji": "🌳", "color": "#81C784"},
    {"id": 6, "text": "fish",  "emoji": "🐟", "color": "#4DD0E1"},
    {"id": 7, "text": "apple", "emoji": "🍎", "color": "#E57373"},
]

MAX_SPAN = 10
ROUNDS_PER_GAME = 5


def items_for_mode(mode: str):
    """Return the active item library for the chosen mode."""
    return WORDS if mode == "words" else PADS


def difficulty_settings(level: str) -> dict:
    return {
        "easy":   {"start_len": 3, "tone_ms": 600},
        "medium": {"start_len": 5, "tone_ms": 500},
        "hard":   {"start_len": 7, "tone_ms": 420},
    }.get(level, {"start_len": 3, "tone_ms": 600})


# ---------------------------------------------------------------------------
# Page-local CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
.aud-title { font-size: 2.4rem; text-align: center; margin: 0.4rem 0 1rem 0; }
.round-pill {
    display: inline-block; padding: 0.4rem 1rem; border-radius: 999px;
    background: var(--app-panel-alt); color: var(--app-text);
    border: 1px solid var(--app-border); font-weight: 600;
}
.recall-progress { font-size: 1.4rem; text-align: center; margin: 0.6rem 0; }
.recall-progress span { margin: 0 0.3rem; }
.feedback-correct { color: var(--app-success); font-weight: 700; font-size: 1.4rem; text-align: center; }
.feedback-wrong   { color: var(--app-danger);  font-weight: 700; font-size: 1.4rem; text-align: center; }
.aud-pad {
    height: 130px; border-radius: 22px;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    color: white; box-shadow: 0 6px 18px rgba(0,0,0,0.25);
    font-weight: 700;
}
.aud-pad-emoji { font-size: 3rem; line-height: 1; }
.aud-pad-name  { font-size: 1.05rem; margin-top: 0.3rem; letter-spacing: 0.06em; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def init_state():
    ss = st.session_state
    ss.setdefault("aud_phase", "setup")        # setup | playback | recall | round_done | results
    ss.setdefault("aud_mode", "tones")         # "tones" (existing) | "words" (new)
    ss.setdefault("aud_difficulty", "easy")
    ss.setdefault("aud_sequence", [])
    ss.setdefault("aud_user_input", [])
    ss.setdefault("aud_round", 0)
    ss.setdefault("aud_correct_rounds", 0)
    ss.setdefault("aud_total_rounds", 0)
    ss.setdefault("aud_max_span", 0)
    ss.setdefault("aud_start_time", None)
    ss.setdefault("aud_round_message", "")
    # Used as a nonce for the visual-flash iframe so the animation re-runs
    # when the child clicks "Play it again".
    ss.setdefault("aud_played_count", 0)


def reset_state():
    for k in [
        "aud_phase", "aud_sequence", "aud_user_input", "aud_round",
        "aud_correct_rounds", "aud_total_rounds", "aud_max_span",
        "aud_start_time", "aud_round_message", "aud_played_count",
    ]:
        st.session_state.pop(k, None)
    # Note: we deliberately keep aud_mode and aud_difficulty so the child
    # can replay the same activity without re-picking it.
    init_state()


init_state()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def new_sequence(length: int, mode: str = "tones") -> list:
    """Build a sequence of item indices for the active activity.

    Indices refer to either ``PADS`` (tones mode) or ``WORDS`` (words mode).
    We avoid two identical items back-to-back so successive tones don't blur
    and successive spoken words don't sound like a stutter.
    """
    library = items_for_mode(mode)
    seq = []
    while len(seq) < length:
        idx = random.randint(0, len(library) - 1)
        if not seq or seq[-1] != idx:
            seq.append(idx)
    return seq


def pad_freqs(seq: list) -> list:
    return [PADS[i]["freq"] for i in seq]


def word_texts(seq: list) -> list:
    return [WORDS[i]["text"] for i in seq]


def item_label(idx: int, mode: str) -> str:
    """Human-readable label for an item, used in feedback strings."""
    if mode == "words":
        return WORDS[idx]["text"]
    return PADS[idx]["name"]


def render_visual_playback(sequence: list, tone_ms: int, nonce: int):
    """Pure-visual flashing of the pads in sync with the audio sequence.

    Audio is emitted separately via ``play_sequence_now`` (its own iframe)
    so it is not tied to this component's mount lifecycle.

    ``nonce`` must change on every replay (e.g. ``aud_played_count``) so
    Streamlit remounts this ``components.html`` iframe; otherwise the HTML
    string is identical and the inner ``<script>`` never runs again — audio
    replays but the pads do not light up.
    """
    pads_js = ",".join(
        f"{{id:{p['id']}, color:'{p['color']}', label:'{p['label']}', name:'{p['name']}'}}"
        for p in PADS
    )
    seq_js = ",".join(str(s) for s in sequence)
    bg = "#0E1422" if st.session_state.get("ui_theme", "light") == "dark" else "#F5F8FC"
    text_color = "#F2F5FA" if st.session_state.get("ui_theme", "light") == "dark" else "#1A202C"

    html = f"""
    <div id="aud-stage" data-nonce="{nonce}" style="
        background:{bg}; color:{text_color};
        padding:1.2rem; border-radius:18px;
        text-align:center; font-family:'Comic Sans MS',sans-serif;">
      <div id="aud-status" style="font-size:1.4rem; font-weight:700; margin-bottom:0.8rem;">
        🎵 Listen carefully…
      </div>
      <div id="aud-pads" style="
            display:grid; grid-template-columns:repeat({len(PADS)}, 130px);
            gap:14px; justify-content:center;">
      </div>
    </div>
    <script>
      const pads = [{pads_js}];
      const seq  = [{seq_js}];
      const padArea = document.getElementById('aud-pads');
      const status  = document.getElementById('aud-status');

      pads.forEach(p => {{
        const el = document.createElement('div');
        el.id = 'pad-' + p.id;
        el.style.height = '130px';
        el.style.borderRadius = '22px';
        el.style.background = p.color;
        el.style.opacity = 0.55;
        el.style.boxShadow = '0 6px 18px rgba(0,0,0,0.25)';
        el.style.transition = 'opacity 120ms ease, transform 120ms ease';
        el.style.display = 'flex';
        el.style.flexDirection = 'column';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.color = 'white';
        el.innerHTML = '<div style="font-size:2.6rem;line-height:1;">' + p.label +
                       '</div><div style="font-weight:700;margin-top:0.3rem;">' + p.name + '</div>';
        padArea.appendChild(el);
      }});

      function flash(idx) {{
        const pad = pads[idx];
        const el = document.getElementById('pad-' + pad.id);
        el.style.opacity = 1;
        el.style.transform = 'scale(1.06)';
        setTimeout(() => {{
          el.style.opacity = 0.55;
          el.style.transform = 'scale(1)';
        }}, {tone_ms});
      }}

      const gap = {tone_ms} + 220;
      seq.forEach((idx, i) => {{
        setTimeout(() => flash(idx), 60 + i * gap);
      }});
      const total = 60 + seq.length * gap;
      setTimeout(() => {{
        status.textContent = '✅ Now repeat the sounds!';
      }}, total);
    </script>
    """
    components.html(html, height=260, scrolling=False)


def render_word_visual_playback(sequence: list, nonce: int) -> None:
    """Light-up word cards in lock-step with the spoken sequence.

    Sync model
    ----------
    The audio is produced by ``speak_sequence_now`` (browser TTS) which
    emits one ``SpeechSynthesisUtterance`` per word and broadcasts
    ``word-start`` / ``word-end`` messages on the ``aud-sync``
    ``BroadcastChannel`` from each utterance's actual ``onstart`` /
    ``onend`` events. This iframe lights/dims the corresponding tile
    directly in response to those messages, so the highlight is sample-
    accurate regardless of browser/voice timing.

    The 220 ms ease-out CSS transition softens the on/off ramp so each
    light fades smoothly rather than snapping.
    """
    pads_js = ",".join(
        f"{{id:{w['id']}, color:'{w['color']}', emoji:'{w['emoji']}', "
        f"text:'{w['text'].capitalize()}'}}"
        for w in WORDS
    )
    seq_js = ",".join(str(s) for s in sequence)
    bg = "#0E1422" if st.session_state.get("ui_theme", "light") == "dark" else "#F5F8FC"
    text_color = "#F2F5FA" if st.session_state.get("ui_theme", "light") == "dark" else "#1A202C"
    html = f"""
    <div data-nonce="{nonce}"
         id="aud-word-stage"
         style="background:{bg}; color:{text_color};
                padding:1.4rem 1.4rem 1.6rem 1.4rem; border-radius:18px;
                text-align:center; font-family:'Comic Sans MS',sans-serif;">
      <div id="aud-word-status" style="font-size:1.3rem; font-weight:700;
                                       margin: 0.2rem 0 1.1rem 0;">
        🎧 Listen carefully…
      </div>
      <div id="aud-word-pads"
           style="display:grid; grid-template-columns:repeat(4, 1fr);
                  gap:18px; justify-content:center;">
      </div>
    </div>
    <script>
      (function() {{
        const pads = [{pads_js}];
        const seq  = [{seq_js}];
        const padArea = document.getElementById('aud-word-pads');
        const status  = document.getElementById('aud-word-status');
        if (!padArea) return;
        padArea.innerHTML = '';
        pads.forEach(w => {{
          const el = document.createElement('div');
          el.id = 'aud-word-' + w.id;
          el.style.cssText = `
              height:130px; border-radius:22px;
              background:${{w.color}}; opacity:0.55;
              box-shadow:0 6px 18px rgba(0,0,0,0.25);
              transition: opacity 220ms cubic-bezier(0.22, 0.61, 0.36, 1),
                          transform 220ms cubic-bezier(0.22, 0.61, 0.36, 1);
              display:flex; flex-direction:column;
              align-items:center; justify-content:center;
              gap:0.45rem;
              color:white; font-weight:700;`;
          el.innerHTML = '<div style="font-size:2.4rem;line-height:1;">' +
                         w.emoji + '</div>' +
                         '<div style="font-size:1.05rem; line-height:1;">' +
                         w.text + '</div>';
          padArea.appendChild(el);
        }});

        function flashOn(padIdx) {{
          const el = document.getElementById('aud-word-' + pads[padIdx].id);
          if (!el) return;
          el.style.opacity = '1';
          el.style.transform = 'scale(1.08)';
        }}
        function flashOff(padIdx) {{
          const el = document.getElementById('aud-word-' + pads[padIdx].id);
          if (!el) return;
          el.style.opacity = '0.55';
          el.style.transform = 'scale(1)';
        }}

        // Listen to per-word audio events emitted by the speech iframe.
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
              if (d.position === seq.length - 1 && status) {{
                status.textContent = '✅ Now repeat the words!';
              }}
            }}
          }};
        }}

        // Fallback: if no message arrives within ~1.4 s, run a timer-based
        // sequence so the child still sees feedback. This only kicks in on
        // browsers without BroadcastChannel or with disabled SpeechSynth.
        const word_ms_est = 700;
        setTimeout(function() {{
          if (lastSeen !== -1) return;          // events arrived → we're fine
          seq.forEach((padIdx, i) => {{
            setTimeout(() => flashOn(padIdx),  i * word_ms_est);
            setTimeout(() => flashOff(padIdx), i * word_ms_est + (word_ms_est - 100));
          }});
          setTimeout(() => {{
            if (status) status.textContent = '✅ Now repeat the words!';
          }}, seq.length * word_ms_est);
        }}, 1400);
      }})();
    </script>
    """
    components.html(html, height=400, scrolling=False)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

db = DatabaseHandler()
user_id = SessionManager.get_user_id()
user_name = SessionManager.get_user_name() or "Friend"
is_child_mode = st.session_state.get("app_mode", "child") == "child"

with st.sidebar:
    st.markdown(f"### 👋 Hi, {user_name}!")
    total_stars = db.get_total_stars(user_id)
    st.markdown(f"### ⭐ Stars: {total_stars}")
    st.divider()
    render_theme_toggle(location="sidebar", key_suffix="aud")
    st.divider()
    if st.button("🏠 Go Home", use_container_width=True, key="aud_home"):
        reset_state()
        st.switch_page("app.py")
    if st.button("🎮 All Games", use_container_width=True, key="aud_all"):
        reset_state()
        st.switch_page("pages/3_Learning_Support.py")


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

st.markdown('<p class="aud-title">🔊 Sound Memory Game</p>', unsafe_allow_html=True)

phase = st.session_state.aud_phase
mode = st.session_state.aud_mode

# ===== Setup =====
if phase == "setup":
    st.markdown(
        f"""
        <div class="instruction-box">
            <strong>👋 Hi {user_name}!</strong><br><br>
            Pick an activity and a difficulty, then we'll start. Each activity
            trains the <em>phonological loop</em> — the part of memory that holds
            sounds and words while you reason about them.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Activity / mode picker (NEW) -------------------------------------
    st.markdown("### 🎚 Pick an activity")
    mcols = st.columns(2)
    with mcols[0]:
        is_tones = mode == "tones"
        if st.button(
            "🔊 Coloured Sounds\n(tones — original game)",
            key="aud_mode_tones",
            type="primary" if is_tones else "secondary",
            use_container_width=True,
        ):
            st.session_state.aud_mode = "tones"
            st.rerun()
    with mcols[1]:
        is_words = mode == "words"
        if st.button(
            "📢 Spoken Words\n(listen and repeat)",
            key="aud_mode_words",
            type="primary" if is_words else "secondary",
            use_container_width=True,
        ):
            st.session_state.aud_mode = "words"
            st.rerun()

    if mode == "words":
        st.markdown(
            """
            <div class="instruction-box" style="margin-top:0.6rem">
                <strong>📢 Spoken-Word Memory</strong><br>
                The computer reads a sequence of simple words aloud
                (<em>cat, dog, ball, sun, book, tree, fish, apple</em>).<br>
                Listen carefully, then tap the words in the <strong>exact same order</strong>.<br>
                Each tap also says the word back to you.
                <br><br>
                <em>Make sure your speakers/headphones are on. Chrome and Edge work best.</em>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="instruction-box" style="margin-top:0.6rem">
                <strong>🔊 Coloured-Sound Memory</strong><br>
                The computer plays a sequence of coloured tones. As you listen,
                say the colour names in your head: <em>“blue, green, red…”</em><br>
                Then tap the pads in the same order. Each tap plays its tone back to you.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- Difficulty -------------------------------------------------------
    st.markdown("### 🎯 Choose difficulty")
    if mode == "words":
        # As requested: Easy = 3, Hard = 7, with Medium = 5 in between.
        unit_word = "words"
    else:
        unit_word = "sounds"
    cols = st.columns(3)
    levels = [
        ("easy",   "😊 Easy",   f"3 {unit_word} to start"),
        ("medium", "🤔 Medium", f"5 {unit_word} to start"),
        ("hard",   "💪 Hard",   f"7 {unit_word} to start"),
    ]
    for col, (lvl, label, desc) in zip(cols, levels):
        with col:
            picked = st.session_state.aud_difficulty == lvl
            if st.button(f"{label}\n{desc}", key=f"diff_{lvl}", use_container_width=True,
                         type="primary" if picked else "secondary"):
                st.session_state.aud_difficulty = lvl
                st.rerun()
    cfg = difficulty_settings(st.session_state.aud_difficulty)
    st.info(
        f"Selected: **{st.session_state.aud_difficulty.upper()}** — "
        f"sequence starts at **{cfg['start_len']} {unit_word}**, "
        f"each correct round adds one more (up to {MAX_SPAN})."
    )

    if st.button("🚀 Start playing!", type="primary", use_container_width=True, key="aud_start"):
        cfg = difficulty_settings(st.session_state.aud_difficulty)
        st.session_state.aud_sequence = new_sequence(cfg["start_len"], mode=mode)
        st.session_state.aud_user_input = []
        st.session_state.aud_round = 1
        st.session_state.aud_correct_rounds = 0
        st.session_state.aud_total_rounds = 0
        st.session_state.aud_max_span = cfg["start_len"]
        st.session_state.aud_start_time = time.time()
        st.session_state.aud_round_message = ""
        st.session_state.aud_phase = "playback"
        st.rerun()

# ===== Playback =====
elif phase == "playback":
    cfg = difficulty_settings(st.session_state.aud_difficulty)
    seq = st.session_state.aud_sequence
    st.markdown(
        f'<div style="text-align:center"><span class="round-pill">'
        f'Round {st.session_state.aud_round} • Sequence length: {len(seq)}'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    # Bump the nonce on every render of the playback phase so the iframe
    # re-mounts (=> the flash animation re-runs) when "Play it again" or
    # the natural entry to playback fires.
    st.session_state.aud_played_count += 1
    nonce = st.session_state.aud_played_count

    if mode == "words":
        words = word_texts(seq)
        # Speak the sequence aloud via Web Speech API.
        speak_sequence_now(words)
        # Visual flashing word cards — same style used in the Final
        # Assessment so the training tab feels consistent.
        render_word_visual_playback(seq, nonce=nonce)
        # Words: ~700ms per word at our rate, plus a small buffer.
        total_ms = max(2000, len(seq) * 800)
    else:
        # Audio in main DOM (autoplay) + visual flashing in iframe.
        play_sequence_now(pad_freqs(seq), tone_ms=cfg["tone_ms"], gap_ms=220)
        render_visual_playback(seq, cfg["tone_ms"], nonce=nonce)
        total_ms = sequence_total_ms(len(seq), tone_ms=cfg["tone_ms"], gap_ms=220)

    st.markdown(
        f'<div style="text-align:center; margin: 1.0rem 0 0.6rem 0; '
        f'color:var(--app-muted);">'
        f'After the sounds finish (~{total_ms/1000:.1f}s) click <strong>I\'m ready</strong>.</div>',
        unsafe_allow_html=True,
    )
    # Side-by-side action buttons with a gap between them so they don't
    # feel stacked-and-squished beneath the playback iframe.
    btn_cols = st.columns([3, 2])
    with btn_cols[0]:
        if st.button("👉 I'm ready — let me repeat", type="primary",
                     use_container_width=True, key="aud_ready"):
            st.session_state.aud_user_input = []
            st.session_state.aud_phase = "recall"
            st.rerun()
    with btn_cols[1]:
        # The click itself already triggers a Streamlit rerun, which lands
        # us back in the playback phase and re-fires play_sequence_now /
        # speak_sequence_now. Calling st.rerun() inside the click body
        # would cause a SECOND rerun in quick succession — Chrome then
        # sees two <audio autoplay> insertions back-to-back and may
        # cancel both, so the user perceives the button as "not
        # responding". The empty body is intentional.
        if st.button("🔁 Play it again", use_container_width=True, key="aud_replay"):
            pass

# ===== Recall =====
elif phase == "recall":
    seq = st.session_state.aud_sequence
    typed = st.session_state.aud_user_input
    st.markdown(
        f'<div style="text-align:center"><span class="round-pill">'
        f'Round {st.session_state.aud_round} • Tap in order'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    progress = ""
    for i in range(len(seq)):
        if i < len(typed):
            progress += "🟩 "
        elif i == len(typed):
            progress += "🟦 "
        else:
            progress += "⬜ "
    st.markdown(f'<div class="recall-progress">{progress}</div>', unsafe_allow_html=True)

    if mode == "words":
        # 8 word pads in a 2-row × 4-column layout.
        ROW_LEN = 4
        for row_start in range(0, len(WORDS), ROW_LEN):
            row_items = WORDS[row_start: row_start + ROW_LEN]
            row_cols = st.columns(ROW_LEN)
            for j, w in enumerate(row_items):
                with row_cols[j]:
                    st.markdown(
                        f"""
                        <div class="aud-pad" style="background:{w['color']};">
                            <div class="aud-pad-emoji">{w['emoji']}</div>
                            <div class="aud-pad-name">{w['text'].capitalize()}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        f"Tap {w['text'].capitalize()}",
                        key=f"word_btn_{w['id']}_{len(typed)}",
                        use_container_width=True,
                    ):
                        queue_speech(w["text"])  # echo the word back
                        typed.append(w["id"])
                        st.session_state.aud_user_input = typed
                        if len(typed) == len(seq):
                            is_correct = typed == seq
                            st.session_state.aud_total_rounds += 1
                            if is_correct:
                                st.session_state.aud_correct_rounds += 1
                                st.session_state.aud_round_message = "correct"
                                st.session_state.aud_max_span = max(
                                    st.session_state.aud_max_span, len(seq)
                                )
                            else:
                                st.session_state.aud_round_message = "wrong"
                            st.session_state.aud_phase = "round_done"
                        st.rerun()
    else:
        pad_cols = st.columns(len(PADS))
        for i, p in enumerate(PADS):
            with pad_cols[i]:
                st.markdown(
                    f"""
                    <div class="aud-pad" style="background:{p['color']};">
                        <div class="aud-pad-emoji">{p['label']}</div>
                        <div class="aud-pad-name">{p['name']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(f"Tap {p['name']}", key=f"pad_btn_{i}_{len(typed)}",
                             use_container_width=True):
                    queue_tone(p["freq"], duration_ms=380)
                    typed.append(i)
                    st.session_state.aud_user_input = typed
                    if len(typed) == len(seq):
                        is_correct = typed == seq
                        st.session_state.aud_total_rounds += 1
                        if is_correct:
                            st.session_state.aud_correct_rounds += 1
                            st.session_state.aud_round_message = "correct"
                            st.session_state.aud_max_span = max(
                                st.session_state.aud_max_span, len(seq)
                            )
                        else:
                            st.session_state.aud_round_message = "wrong"
                        st.session_state.aud_phase = "round_done"
                    st.rerun()

    cleft, cright = st.columns(2)
    with cleft:
        if st.button("↩ Reset this round's taps", key="aud_reset_taps",
                     use_container_width=True):
            st.session_state.aud_user_input = []
            st.rerun()
    with cright:
        if st.button("🔁 Hear sequence again", key="aud_recall_replay",
                     use_container_width=True):
            cfg = difficulty_settings(st.session_state.aud_difficulty)
            if mode == "words":
                queue_speech(word_texts(seq))
            else:
                queue_sequence(pad_freqs(seq), tone_ms=cfg["tone_ms"], gap_ms=220)
            st.rerun()

# ===== Round done =====
elif phase == "round_done":
    correct = st.session_state.aud_round_message == "correct"
    if correct:
        st.markdown('<p class="feedback-correct">🎉 Yes! That was perfect!</p>',
                    unsafe_allow_html=True)
        st.balloons()
    else:
        right_seq = " → ".join(
            item_label(i, mode).capitalize()
            for i in st.session_state.aud_sequence
        )
        st.markdown(
            f'<p class="feedback-wrong">Oops, not quite. The sequence was:<br>'
            f'<strong>{right_seq}</strong></p>',
            unsafe_allow_html=True,
        )

    rounds_played = st.session_state.aud_total_rounds

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Round", f"{rounds_played} / {ROUNDS_PER_GAME}")
    with col_b:
        st.metric("Best length", st.session_state.aud_max_span)

    if rounds_played >= ROUNDS_PER_GAME:
        if st.button("🏁 See my results", type="primary",
                     use_container_width=True, key="aud_finish"):
            st.session_state.aud_phase = "results"
            st.rerun()
    else:
        if st.button("➡ Next round", type="primary",
                     use_container_width=True, key="aud_next"):
            new_len = len(st.session_state.aud_sequence) + (1 if correct else 0)
            new_len = max(min(new_len, MAX_SPAN), len(st.session_state.aud_sequence))
            st.session_state.aud_sequence = new_sequence(new_len, mode=mode)
            st.session_state.aud_user_input = []
            st.session_state.aud_round += 1
            st.session_state.aud_phase = "playback"
            st.rerun()
        if st.button("🏁 Stop and see results", key="aud_stop_now",
                     use_container_width=True):
            st.session_state.aud_phase = "results"
            st.rerun()

# ===== Results =====
elif phase == "results":
    total = max(st.session_state.aud_total_rounds, 1)
    correct = st.session_state.aud_correct_rounds
    accuracy = correct / total
    elapsed = time.time() - (st.session_state.aud_start_time or time.time())
    stars = db.calculate_stars_for_accuracy(accuracy)
    star_icons = "⭐" * stars

    st.markdown(
        f"""
        <div class="encouragement">
            🎉 Great job, {user_name}! You earned {star_icons} ({stars} stars).
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Correct rounds", f"{correct} / {total}")
    c2.metric("Accuracy", f"{accuracy * 100:.0f}%")
    c3.metric("Best sequence", st.session_state.aud_max_span)

    # Tag the difficulty with the mode so teacher history makes the activity
    # explicit (e.g. "easy-words" vs "easy-tones").
    diff_tag = f"{st.session_state.aud_difficulty}-{mode}"
    db.record_auditory_memory_result(
        user_id=user_id,
        sequence_length=st.session_state.aud_max_span,
        total_rounds=total,
        correct_rounds=correct,
        accuracy=accuracy,
        time_spent_seconds=elapsed,
        difficulty_level=diff_tag,
        max_span_reached=st.session_state.aud_max_span,
    )
    db.record_session(
        user_id=user_id,
        module_name="auditory_memory",
        accuracy=accuracy,
        time_spent_seconds=elapsed,
        score=correct,
        max_score=total,
    )
    activity_label = "Word memory" if mode == "words" else "Sound memory"
    db.award_stars(
        user_id=user_id,
        module_name="auditory_memory",
        stars=stars,
        reason=f"{activity_label} ({st.session_state.aud_difficulty}) - {accuracy*100:.0f}%",
    )

    st.markdown("---")
    n1, n2, n3 = st.columns(3)
    with n1:
        if st.button("🔄 Play again", type="primary", use_container_width=True, key="aud_again"):
            reset_state()
            st.rerun()
    with n2:
        if st.button("🧩 Visual memory", use_container_width=True, key="aud_to_vis"):
            reset_state()
            st.switch_page("pages/5_Visual_Memory.py")
    with n3:
        if st.button("🏠 Home", use_container_width=True, key="aud_to_home"):
            reset_state()
            st.switch_page("app.py")

# Teacher mode notes
if not is_child_mode:
    st.divider()
    st.markdown("### 👨‍🏫 Teacher / Parent notes")
    st.write(
        "This module trains the **phonological loop** — the working-memory "
        "subsystem that briefly holds spoken or sub-vocalised material. The "
        "child hears a tone-and-colour sequence and reproduces it; success "
        "extends the span by one. Difficulty controls the starting length "
        "(Easy 3 / Medium 5 / Hard 7). The longest correctly-recalled "
        "sequence is the most useful clinical metric."
    )
    history = db.get_auditory_memory_history(user_id, limit=10)
    if history:
        st.markdown("Recent sessions:")
        for h in history:
            acc = h.get("accuracy") or 0
            st.write(
                f"- {h.get('created_at', '')[:16]} — "
                f"{h.get('difficulty_level', '?')} • span {h.get('max_span_reached', '?')} • "
                f"{acc*100:.0f}%"
            )
