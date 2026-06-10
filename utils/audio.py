"""
Audio helpers — generate sine-wave WAV bytes server-side and emit
``<audio autoplay>`` directly into the main page DOM.

Why not Web Audio API in components.html?
----------------------------------------
Streamlit's ``components.html`` renders inside an iframe. Browsers require
a fresh user gesture inside that iframe to start an AudioContext, so per-tap
sounds (or any sound triggered by ``st.button`` followed by ``st.rerun()``)
silently fail because the iframe is recreated *after* the gesture.

Instead, we build the audio as a sine-wave WAV in Python, base64 encode it
into a ``data:audio/wav;base64,...`` URL, and inject ``<audio autoplay>``
into the parent document via ``st.markdown(unsafe_allow_html=True)``. That
element inherits the user-gesture activation from the click that triggered
the rerun, and the audio plays reliably.

Usage
-----
1. Call :func:`render_audio_queue` once near the top of your page (after
   ``apply_theme()``).
2. From any button handler, call :func:`queue_tone` or :func:`queue_sequence`
   *before* calling ``st.rerun()``.

The queued snippet is consumed exactly once on the next render.
"""

from __future__ import annotations

import base64
import io
import json
import math
import struct
import wave
from typing import Iterable, List, Tuple

import streamlit as st
import streamlit.components.v1 as _components

try:  # pragma: no cover - numpy is already a transitive dep on Streamlit
    import numpy as np
    _HAS_NUMPY = True
except Exception:  # pragma: no cover
    _HAS_NUMPY = False


SAMPLE_RATE = 22_050
DEFAULT_VOLUME = 0.30
QUEUE_KEY = "_audio_html_queue"
NONCE_KEY = "_audio_html_nonce"


# ---------------------------------------------------------------------------
# WAV generation
# ---------------------------------------------------------------------------

def _tone_samples(freq_hz: float, duration_ms: int, volume: float) -> List[int]:
    n = int(SAMPLE_RATE * duration_ms / 1000)
    fade = max(1, int(SAMPLE_RATE * 0.012))  # 12 ms attack/release

    if _HAS_NUMPY:
        i = np.arange(n)
        env = np.minimum(np.minimum(i / fade, (n - i) / fade), 1.0)
        env = np.clip(env, 0.0, 1.0)
        s = (volume * env * 32767 *
             np.sin(2 * np.pi * freq_hz * i / SAMPLE_RATE)).astype(np.int16)
        return s.tolist()

    out: List[int] = []
    for k in range(n):
        env = 1.0
        if k < fade:
            env = k / fade
        elif k > n - fade:
            env = max(0.0, (n - k) / fade)
        sample = int(volume * env * 32767 *
                     math.sin(2 * math.pi * freq_hz * k / SAMPLE_RATE))
        out.append(sample)
    return out


def _silence_samples(duration_ms: int) -> List[int]:
    return [0] * int(SAMPLE_RATE * duration_ms / 1000)


def _wav_bytes(samples: List[int]) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        if _HAS_NUMPY:
            w.writeframes(np.array(samples, dtype=np.int16).tobytes())
        else:
            w.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return buf.getvalue()


@st.cache_data(show_spinner=False, max_entries=64)
def make_tone_wav(freq_hz: float, duration_ms: int = 400,
                  volume: float = DEFAULT_VOLUME) -> bytes:
    """Cached: generate a single-tone WAV (mono, 16-bit, 22.05 kHz)."""
    return _wav_bytes(_tone_samples(freq_hz, duration_ms, volume))


@st.cache_data(show_spinner=False, max_entries=64)
def make_sequence_wav(freqs: Tuple[float, ...], tone_ms: int = 500,
                      gap_ms: int = 220, volume: float = DEFAULT_VOLUME) -> bytes:
    """Cached: generate a WAV with multiple tones separated by silence."""
    samples: List[int] = []
    for i, f in enumerate(freqs):
        if i > 0:
            samples.extend(_silence_samples(gap_ms))
        samples.extend(_tone_samples(f, tone_ms, volume))
    return _wav_bytes(samples)


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def _audio_tag(wav: bytes, nonce: int) -> str:
    """Plain ``<audio autoplay>`` tag for the queue-based code-path.

    Used by :func:`render_audio_queue`, which renders this snippet exactly
    once after a state-change ``st.rerun()``. In that one-shot context the
    element is freshly inserted into the DOM, so the browser's ``autoplay``
    attribute fires reliably.
    """
    b64 = base64.b64encode(wav).decode("ascii")
    return (
        f'<audio id="aud-elem-{nonce}" autoplay '
        f'data-nonce="{nonce}" '
        f'src="data:audio/wav;base64,{b64}" '
        f'style="display:none;height:0;width:0"></audio>'
    )


def _audio_play_iframe(wav: bytes, nonce: int, height: int = 0) -> None:
    """Force-play ``wav`` *now*, bypassing React reconciliation.

    Why this exists
    ---------------
    When ``play_*_now`` is called inside a phase that re-renders on every
    rerun (e.g. the Auditory Memory playback phase), ``st.markdown`` writes
    an updated audio HTML snippet at the same script position on each run.
    React/Streamlit may *patch attributes* on the existing ``<audio>``
    element rather than recreating it — and changing ``src`` on an existing
    ``<audio>`` element does **not** retrigger ``autoplay``, so the user
    sees "Play it again" as silently doing nothing.

    Solution: render an iframe (via ``components.html``, where ``<script>``
    blocks actually execute) that creates a brand-new
    ``HTMLAudioElement`` programmatically and calls ``.play()`` on it. The
    nonce makes the iframe content unique on every call, guaranteeing a
    fresh iframe mount and therefore a fresh ``Audio`` instance every
    time. ``play()`` succeeds because Chromium-family and Firefox
    propagate user-activation to scripts that run shortly after a click.
    """
    b64 = base64.b64encode(wav).decode("ascii")
    _components.html(
        f"""
        <div data-aud-nonce="{nonce}" style="display:none"></div>
        <script>
          (function() {{
            try {{
              var a = new Audio('data:audio/wav;base64,{b64}');
              a.volume = 1.0;
              var p = a.play();
              if (p && p.catch) {{
                p.catch(function(e) {{
                  // If autoplay is blocked we can't do much from inside an
                  // iframe — log to console and let the (timer-based)
                  // visual fallback keep the game usable.
                  try {{ console.warn('audio.play() blocked:', e); }} catch (_) {{}}
                }});
              }}
            }} catch (e) {{
              try {{ console.warn('audio init failed:', e); }} catch (_) {{}}
            }}
          }})();
        </script>
        """,
        height=height,
    )


def _next_nonce() -> int:
    """Force a fresh DOM node per emission so Streamlit re-mounts the element."""
    n = int(st.session_state.get(NONCE_KEY, 0)) + 1
    st.session_state[NONCE_KEY] = n
    return n


# ---------------------------------------------------------------------------
# Public API: queue (for use before st.rerun) + render
# ---------------------------------------------------------------------------

def queue_tone(freq_hz: float, duration_ms: int = 400) -> None:
    """Queue a single tone to play on the next render. Safe to call before st.rerun()."""
    st.session_state[QUEUE_KEY] = _audio_tag(
        make_tone_wav(freq_hz, duration_ms), _next_nonce()
    )


def queue_sequence(freqs: Iterable[float], tone_ms: int = 500,
                   gap_ms: int = 220) -> None:
    """Queue a tone-sequence to play on the next render."""
    st.session_state[QUEUE_KEY] = _audio_tag(
        make_sequence_wav(tuple(freqs), tone_ms, gap_ms), _next_nonce()
    )


def render_audio_queue() -> None:
    """Render and consume any queued ``<audio>`` snippet. Call once per page."""
    snippet = st.session_state.pop(QUEUE_KEY, None)
    if snippet:
        st.markdown(snippet, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Public API: play immediately (use when NOT followed by st.rerun)
# ---------------------------------------------------------------------------

def play_tone_now(freq_hz: float, duration_ms: int = 400) -> None:
    """Play a single tone immediately, even if called in a re-rendering phase."""
    _audio_play_iframe(make_tone_wav(freq_hz, duration_ms), _next_nonce())


def play_sequence_now(freqs: Iterable[float], tone_ms: int = 500,
                      gap_ms: int = 220) -> None:
    """Play a tone sequence immediately, even if called in a re-rendering phase.

    Each call results in a brand-new HTMLAudioElement created in JS and
    explicitly ``.play()``-ed, so "Play it again" reliably re-fires the
    sound without any page refresh.
    """
    _audio_play_iframe(
        make_sequence_wav(tuple(freqs), tone_ms, gap_ms), _next_nonce()
    )


def sequence_total_ms(num_tones: int, tone_ms: int = 500, gap_ms: int = 220) -> int:
    """Total audible length of a tone-sequence in milliseconds."""
    if num_tones <= 0:
        return 0
    return num_tones * tone_ms + max(0, num_tones - 1) * gap_ms


# ---------------------------------------------------------------------------
# Browser SpeechSynthesis (TTS) — for spoken-word activities
# ---------------------------------------------------------------------------
#
# We use the Web Speech API (``window.speechSynthesis``) inside a small
# ``components.html`` iframe. Although the iframe is recreated on each rerun,
# the SpeechSynthesis queue is *browser-global*, so once an utterance is
# ``speak()``-ed it keeps playing even if the iframe is unmounted moments
# later. This is why per-tap word feedback survives Streamlit's normal
# rerun lifecycle — unlike ``AudioContext`` which is iframe-bound.
#
# The user's recent click counts as user activation, which is required
# before ``speechSynthesis.speak`` will produce sound on most modern
# browsers. We additionally wait for ``voiceschanged`` since some browsers
# load voices asynchronously.

SPEECH_QUEUE_KEY = "_speech_queue"


def queue_speech(text_or_list) -> None:
    """Queue word(s) to be spoken on the next render.

    Accepts a single string or an iterable of strings. Safe to call before
    ``st.rerun()``; the queue is flushed by :func:`render_speech_queue`.
    """
    items = [text_or_list] if isinstance(text_or_list, str) else list(text_or_list)
    existing = list(st.session_state.get(SPEECH_QUEUE_KEY, []))
    st.session_state[SPEECH_QUEUE_KEY] = existing + items


def render_speech_queue() -> None:
    """Render and consume any queued speech. Call once per page (after
    :func:`render_audio_queue`)."""
    queue = st.session_state.pop(SPEECH_QUEUE_KEY, None)
    if queue:
        _emit_speech_iframe(list(queue))


def speak_now(text: str) -> None:
    """Speak immediately inline (use when not followed by ``st.rerun()``)."""
    _emit_speech_iframe([text])


def speak_sequence_now(words: Iterable[str]) -> None:
    """Speak a sequence of words inline."""
    _emit_speech_iframe(list(words))


def _emit_speech_iframe(items: List[str]) -> None:
    """Speak ``items`` aloud, one ``SpeechSynthesisUtterance`` per item, and
    publish per-item ``word-start`` / ``word-end`` messages on the
    ``aud-sync`` BroadcastChannel.

    The visual word-pad iframe lights its tile when ``word-start`` fires and
    dims it when ``word-end`` fires, giving sample-accurate audio↔visual
    sync regardless of voice / browser timing variance.
    """
    nonce = _next_nonce()
    payload = json.dumps(items)
    _components.html(
        f"""
        <div data-speech-nonce="{nonce}" style="display:none"></div>
        <script>
          (function() {{
            if (!window.speechSynthesis) return;
            const items = {payload};
            const nonce = {nonce};
            try {{ speechSynthesis.cancel(); }} catch (e) {{}}

            // Cross-frame broadcaster used by visual word-pad iframes for
            // pixel-perfect highlight timing.
            let ch = null;
            try {{ ch = new BroadcastChannel('aud-sync'); }} catch (e) {{}}
            function bc(msg) {{
              if (!ch) return;
              try {{ ch.postMessage(msg); }} catch (e) {{}}
            }}

            function speakAll() {{
              items.forEach(function(text, idx) {{
                var u = new SpeechSynthesisUtterance(String(text));
                u.rate  = 0.85;
                u.pitch = 1.05;
                u.volume = 1.0;
                u.lang  = 'en-US';
                u.onstart = function() {{
                  bc({{ type: 'word-start', position: idx, nonce: nonce,
                        t: performance.now() }});
                }};
                u.onend = function() {{
                  bc({{ type: 'word-end', position: idx, nonce: nonce,
                        t: performance.now() }});
                  if (idx === items.length - 1 && ch) {{
                    setTimeout(function() {{ try {{ ch.close(); }} catch (e) {{}} }}, 200);
                  }}
                }};
                u.onerror = function() {{
                  // If a word fails to speak, still emit an 'end' so the
                  // visual highlight doesn't get stuck on.
                  bc({{ type: 'word-end', position: idx, nonce: nonce,
                        t: performance.now() }});
                }};
                speechSynthesis.speak(u);
              }});
            }}

            // Some browsers load voices asynchronously.
            if (speechSynthesis.getVoices().length === 0) {{
              var fired = false;
              var go = function() {{
                if (fired) return;
                fired = true;
                speakAll();
              }};
              speechSynthesis.addEventListener('voiceschanged', go, {{ once: true }});
              setTimeout(go, 250); // hard fallback
            }} else {{
              speakAll();
            }}
          }})();
        </script>
        """,
        height=0,
    )
