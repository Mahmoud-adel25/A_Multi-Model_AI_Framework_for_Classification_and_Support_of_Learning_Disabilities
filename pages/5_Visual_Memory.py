"""
Visual Memory Module - Child-Friendly, Fully Implemented

REAL IMPLEMENTATION with:
1. Colorful grid of large letters/symbols
2. Configurable display duration
3. Recall questions with big clickable buttons
4. Positive reinforcement and encouragement
5. Stars awarded based on performance
6. Full accessibility features for dyslexia
7. Progressive difficulty levels
"""

import streamlit as st
import sys
import os
import random
import time
import html
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import SessionManager
from utils.theme import apply_theme, render_theme_toggle
from database.db_handler import DatabaseHandler

# Initialize session
SessionManager.initialize_session()
SessionManager.track_page_visit("visual_memory")

st.set_page_config(
    page_title="Memory Game!",
    page_icon="🧩",
    layout="wide"
)
apply_theme()

# Child-friendly, accessible CSS
st.markdown("""
<style>
@import url('https://fonts.cdnfonts.com/css/opendyslexic');

.stApp {
    font-family: 'OpenDyslexic', 'Comic Sans MS', sans-serif;
    line-height: 1.8;
    letter-spacing: 0.1em;
}

.game-header { font-size: 2.5rem; color: #FF6F00; text-align: center; margin-bottom: 1rem; }
.instruction-box, .how-to-play { color: #000000 !important; font-size: 1.35rem !important; line-height: 1.8 !important; }
.instruction-box strong, .instruction-box p, .instruction-box h3 { color: #000000 !important; }

.memory-grid-cell {
    background: linear-gradient(135deg, #42A5F5 0%, #1E88E5 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    font-size: 2.5rem;
    font-weight: bold;
    margin: 0.5rem;
    min-height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 15px rgba(30, 136, 229, 0.3);
}

.countdown-display {
    font-size: 8rem;
    font-weight: bold;
    text-align: center;
    padding: 2rem;
    border-radius: 20px;
    background: linear-gradient(135deg, #FF6F00 0%, #FF8F00 100%);
    color: white;
    margin: 2rem auto;
    max-width: 300px;
    box-shadow: 0 8px 30px rgba(255, 111, 0, 0.4);
}

.instruction-box {
    background: #FFF3E0;
    padding: 1.5rem;
    border-radius: 15px;
    border: 3px solid #FFB74D;
    font-size: 1.2rem;
    margin: 1rem 0;
    text-align: center;
}

.question-display {
    background: linear-gradient(135deg, #7B1FA2 0%, #9C27B0 100%);
    color: white;
    padding: 2rem;
    border-radius: 20px;
    text-align: center;
    font-size: 1.5rem;
    margin: 1rem 0;
}

.answer-btn {
    font-size: 2rem !important;
    padding: 1.5rem !important;
    margin: 0.5rem !important;
    min-height: 80px !important;
    border-radius: 15px !important;
}

.stars-earned {
    background: linear-gradient(135deg, #FFD54F 0%, #FFC107 100%);
    padding: 2rem;
    border-radius: 20px;
    text-align: center;
    font-size: 2rem;
    margin: 1rem 0;
    box-shadow: 0 8px 25px rgba(255, 193, 7, 0.3);
}

.encouragement {
    background: linear-gradient(135deg, #C8E6C9 0%, #A5D6A7 100%);
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    font-size: 1.5rem;
    color: #2E7D32;
    margin: 1rem 0;
    border: 3px solid #66BB6A;
}

.progress-dots {
    text-align: center;
    font-size: 2rem;
    margin: 1rem 0;
}

.result-correct {
    background: #C8E6C9 !important;
    border: 4px solid #4CAF50 !important;
    color: #2E7D32 !important;
}

.result-incorrect {
    background: #FFCDD2 !important;
    border: 4px solid #F44336 !important;
    color: #C62828 !important;
}

.difficulty-card {
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    margin: 0.5rem;
    cursor: pointer;
    transition: transform 0.2s;
    color: #000000;
}

.difficulty-card:hover {
    transform: scale(1.05);
}

.difficulty-card h3,
.difficulty-card p {
    color: #000000 !important;
}

.diff-easy {
    background: linear-gradient(135deg, #C8E6C9 0%, #A5D6A7 100%);
    border: 3px solid #66BB6A;
}

.diff-medium {
    background: linear-gradient(135deg, #FFF9C4 0%, #FFF176 100%);
    border: 3px solid #FFEE58;
}

.diff-hard {
    background: linear-gradient(135deg, #FFCCBC 0%, #FFAB91 100%);
    border: 3px solid #FF8A65;
}

/* Empty recall grid — highlighted cell (red ring) asks "what was here?" */
.vm-recall-grid-wrap {
    display: flex;
    justify-content: center;
    margin: 1.2rem 0 0.6rem 0;
}
.vm-recall-grid {
    display: grid;
    gap: 10px;
    justify-content: center;
}
.vm-recall-cell {
    background: #FAFAFA;
    border: 2px solid #B0BEC5;
    border-radius: 16px;
    min-height: 76px;
    min-width: 76px;
    box-sizing: border-box;
}
.vm-recall-cell-target {
    background: #FFF8F8;
    border: 4px solid #E53935;
    box-shadow:
        0 0 0 4px rgba(229, 57, 53, 0.22),
        inset 0 0 0 3px rgba(229, 57, 53, 0.12);
    border-radius: 16px;
    min-height: 76px;
    min-width: 76px;
    box-sizing: border-box;
}

/* Large buttons for children */
.stButton > button {
    font-size: 1.3rem;
    padding: 0.8rem 1.5rem;
    border-radius: 15px;
    font-family: 'OpenDyslexic', 'Comic Sans MS', sans-serif;
}
</style>
""", unsafe_allow_html=True)


def initialize_memory_state():
    """Initialize or reset visual memory module state."""
    if 'memory_initialized' not in st.session_state:
        st.session_state.memory_initialized = False
    
    if not st.session_state.memory_initialized:
        st.session_state.memory_phase = 'setup'
        st.session_state.memory_grid = []
        st.session_state.memory_grid_size = 3
        st.session_state.memory_display_duration = 5
        st.session_state.memory_questions = []
        st.session_state.memory_current_question = 0
        st.session_state.memory_answers = []
        st.session_state.memory_correct_count = 0
        st.session_state.memory_start_time = None
        st.session_state.memory_memorize_end = None
        st.session_state.memory_end_time = None
        st.session_state.memory_difficulty = 'easy'
        st.session_state.memory_use_symbols = False
        st.session_state.memory_initialized = True


def generate_memory_grid(grid_size: int, use_symbols: bool = False):
    """Generate a grid of unique, easy-to-read letters or symbols."""
    total_cells = grid_size * grid_size
    
    if use_symbols:
        symbols = ['⭐', '❤️', '🔵', '🟢', '🟡', '🟣', '🔶', '🔷', '⬛']
        if total_cells <= len(symbols):
            return random.sample(symbols, total_cells)
        else:
            return [random.choice(symbols) for _ in range(total_cells)]
    else:
        # Use easy-to-read letters (avoid confusing pairs)
        safe_letters = 'ACEFGHKLMRSTUVX'
        if total_cells <= len(safe_letters):
            return random.sample(safe_letters, total_cells)
        else:
            return [random.choice(safe_letters) for _ in range(total_cells)]


def generate_questions(grid: list, grid_size: int, num_questions: int):
    """Generate recall questions for the memory test."""
    questions = []
    total_cells = grid_size * grid_size
    used_positions = set()
    
    for i in range(num_questions):
        available = [p for p in range(total_cells) if p not in used_positions]
        if not available:
            available = list(range(total_cells))
        
        pos = random.choice(available)
        used_positions.add(pos)
        
        row = pos // grid_size + 1
        col = pos % grid_size + 1
        correct = grid[pos]
        
        # Generate wrong answers from the grid
        wrong_answers = [g for g in grid if g != correct]
        wrong_answers = list(set(wrong_answers))[:3]
        
        # Ensure we have enough options
        while len(wrong_answers) < 3:
            if st.session_state.memory_use_symbols:
                extra = random.choice(['⭐', '❤️', '🔵', '🟢', '🟡'])
            else:
                extra = random.choice('ACEFGHKLMRSTUVX')
            if extra != correct and extra not in wrong_answers:
                wrong_answers.append(extra)
        
        options = wrong_answers[:3] + [correct]
        random.shuffle(options)
        
        use_syms = st.session_state.memory_use_symbols
        qtext = (
            "What shape was in the square with the red ring?"
            if use_syms
            else "What letter was in the square with the red ring?"
        )
        questions.append({
            'question': qtext,
            'position': pos,
            'row': row,
            'col': col,
            'correct_answer': correct,
            'options': options
        })
    
    return questions


def recall_grid_html(grid_size: int, highlight_pos: int) -> str:
    """Empty grid with one cell ringed in red — spatial recall cue."""
    n = grid_size * grid_size
    cols = " ".join(["minmax(64px, 92px)"] * grid_size)
    parts = []
    for i in range(n):
        cls = "vm-recall-cell-target" if i == highlight_pos else "vm-recall-cell"
        parts.append(f'<div class="{cls}"></div>')
    inner = "".join(parts)
    return (
        f'<div class="vm-recall-grid-wrap">'
        f'<div class="vm-recall-grid" style="grid-template-columns: {cols};">'
        f"{inner}</div></div>"
    )


def memorize_grid_html(grid: list, grid_size: int) -> str:
    """Single HTML/CSS grid for the memorise phase.

    Avoids nested ``st.columns`` here: after the setup screen also uses three
    columns for Easy/Medium/Hard, Streamlit can reuse column slots across
    reruns so those buttons sometimes appear *between* memorise rows.
    """
    colors = ["#42A5F5", "#66BB6A", "#FFA726", "#AB47BC", "#EF5350", "#26C6DA"]
    font = "1.85rem" if grid_size >= 4 else "2.5rem"
    pad = "1rem" if grid_size >= 4 else "1.5rem"
    cell_min = "64px" if grid_size >= 4 else "76px"
    cols = " ".join([f"minmax({cell_min}, 1fr)"] * grid_size)
    parts = []
    for i in range(grid_size * grid_size):
        color = colors[i % len(colors)]
        item = html.escape(str(grid[i]))
        parts.append(
            f'<div style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%);'
            f"color: white; padding: {pad}; border-radius: 15px; text-align: center;"
            f"font-size: {font}; font-weight: bold; min-height: 90px; display: flex;"
            f"align-items: center; justify-content: center; margin: 0.15rem;"
            f'box-shadow: 0 4px 15px {color}66;">{item}</div>'
        )
    inner = "".join(parts)
    return (
        f'<div class="vm-recall-grid-wrap">'
        f'<div class="vm-recall-grid" style="grid-template-columns: {cols};">'
        f"{inner}</div></div>"
    )


def get_difficulty_settings(difficulty: str):
    """Get settings based on difficulty level."""
    settings = {
        'easy': {'grid_size': 2, 'display_duration': 8, 'num_questions': 2},
        'medium': {'grid_size': 3, 'display_duration': 6, 'num_questions': 3},
        'hard': {'grid_size': 4, 'display_duration': 5, 'num_questions': 4},
    }
    return settings.get(difficulty, settings['easy'])


def get_encouragement():
    """Get a random encouraging message."""
    messages = [
        "You're doing great! 🌟",
        "Awesome memory! 🧠",
        "Keep going! 💪",
        "Super! 🎉",
        "You got it! ⭐",
        "Amazing! 🚀",
    ]
    return random.choice(messages)


# Initialize state
initialize_memory_state()

# Get user info
user_id = SessionManager.get_user_id()
user_age = SessionManager.get_user_age() or 8
user_name = SessionManager.get_user_name() or "Friend"
db = DatabaseHandler()

# Sidebar
with st.sidebar:
    st.markdown(f"### 👋 Hi, {user_name}!")
    
    total_stars = db.get_total_stars(user_id)
    st.markdown(f"### ⭐ Stars: {total_stars}")
    
    st.divider()
    st.markdown("### 🎨 Appearance")
    render_theme_toggle(location="sidebar", key_suffix="vm")
    st.divider()
    
    if st.button("🏠 Go Home", use_container_width=True):
        st.session_state.memory_initialized = False
        st.switch_page("app.py")
    
    if st.button("🎮 All Games", use_container_width=True):
        st.session_state.memory_initialized = False
        st.switch_page("pages/3_Learning_Support.py")

# Phase: Setup
if st.session_state.memory_phase == 'setup':
    st.markdown('<p class="game-header">🧩 Memory Game! 🧩</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="instruction-box">
        <h3>📋 How to Play:</h3>
        <p>1. Look at the grid and <strong>REMEMBER</strong> where each letter is</p>
        <p>2. The grid will disappear!</p>
        <p>3. Answer questions about what you saw</p>
        <p>4. Earn stars! ⭐</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Difficulty selection
    st.markdown("### 🎯 Choose Difficulty")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="difficulty-card diff-easy">
            <h3>😊 Easy</h3>
            <p>2x2 grid</p>
            <p>8 seconds</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("😊 Easy", use_container_width=True, key="easy_btn"):
            st.session_state.memory_difficulty = 'easy'
    
    with col2:
        st.markdown("""
        <div class="difficulty-card diff-medium">
            <h3>🤔 Medium</h3>
            <p>3x3 grid</p>
            <p>6 seconds</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🤔 Medium", use_container_width=True, key="medium_btn"):
            st.session_state.memory_difficulty = 'medium'
    
    with col3:
        st.markdown("""
        <div class="difficulty-card diff-hard">
            <h3>💪 Hard</h3>
            <p>4x4 grid</p>
            <p>5 seconds</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("💪 Hard", use_container_width=True, key="hard_btn"):
            st.session_state.memory_difficulty = 'hard'
    
    settings = get_difficulty_settings(st.session_state.memory_difficulty)
    
    st.info(f"Selected: **{st.session_state.memory_difficulty.upper()}** - {settings['grid_size']}x{settings['grid_size']} grid, {settings['display_duration']} seconds")
    
    # Symbol option
    use_symbols = st.checkbox("Use shapes instead of letters", value=False)
    st.session_state.memory_use_symbols = use_symbols
    
    # Start button
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 START GAME!", type="primary", use_container_width=True):
        settings = get_difficulty_settings(st.session_state.memory_difficulty)
        
        grid = generate_memory_grid(settings['grid_size'], st.session_state.memory_use_symbols)
        questions = generate_questions(grid, settings['grid_size'], settings['num_questions'])
        
        st.session_state.memory_grid = grid
        st.session_state.memory_grid_size = settings['grid_size']
        st.session_state.memory_display_duration = settings['display_duration']
        st.session_state.memory_questions = questions
        st.session_state.memory_current_question = 0
        st.session_state.memory_answers = []
        st.session_state.memory_correct_count = 0
        st.session_state.memory_start_time = time.time()
        st.session_state.memory_memorize_end = time.time() + settings['display_duration']
        st.session_state.memory_phase = 'memorize'
        st.rerun()

# Phase: Memorize
elif st.session_state.memory_phase == 'memorize':
    time_left = st.session_state.memory_memorize_end - time.time()
    
    if time_left <= 0:
        st.session_state.memory_phase = 'questions'
        st.rerun()
    
    st.markdown('<p class="game-header">👀 Look and Remember! 👀</p>', unsafe_allow_html=True)
    
    # Countdown
    st.markdown(f"""
    <div class="countdown-display">
        {int(time_left) + 1}
    </div>
    """, unsafe_allow_html=True)
    
    # Display grid
    grid = st.session_state.memory_grid
    grid_size = st.session_state.memory_grid_size
    
    st.markdown(memorize_grid_html(grid, grid_size), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; font-size: 1.3rem; color: #666;">
        Pay attention to <strong>where</strong> each item sits — questions will show a square on an empty grid!
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(0.5)
    st.rerun()

# Phase: Questions
elif st.session_state.memory_phase == 'questions':
    questions = st.session_state.memory_questions
    current_q = st.session_state.memory_current_question
    
    if current_q >= len(questions):
        st.session_state.memory_end_time = time.time()
        st.session_state.memory_phase = 'results'
        st.rerun()
    
    question = questions[current_q]
    
    st.markdown('<p class="game-header">🤔 What Do You Remember? 🤔</p>', unsafe_allow_html=True)
    
    # Progress dots
    dots = ""
    for i in range(len(questions)):
        if i < current_q:
            dots += "✅ "
        elif i == current_q:
            dots += "🔵 "
        else:
            dots += "⚪ "
    
    st.markdown(f'<div class="progress-dots">{dots}</div>', unsafe_allow_html=True)
    st.markdown(f"**Question {current_q + 1} of {len(questions)}**")
    
    st.markdown(
        recall_grid_html(
            st.session_state.memory_grid_size,
            question["position"],
        ),
        unsafe_allow_html=True,
    )
    st.markdown(f"""
    <div class="question-display">
        <h2 style="margin: 0;">{question['question']}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Answer options - big buttons
    st.markdown("### Click your answer:")
    
    options = question['options']
    cols = st.columns(len(options))
    
    for i, opt in enumerate(options):
        with cols[i]:
            if st.button(opt, key=f"opt_{current_q}_{i}", use_container_width=True):
                is_correct = opt == question['correct_answer']
                
                st.session_state.memory_answers.append({
                    'question': question['question'],
                    'user_answer': opt,
                    'correct_answer': question['correct_answer'],
                    'is_correct': is_correct
                })
                
                if is_correct:
                    st.session_state.memory_correct_count += 1
                    st.toast(get_encouragement())
                
                st.session_state.memory_current_question += 1
                st.rerun()
    
    # Hint about grid
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background: #E3F2FD; padding: 1rem; border-radius: 10px; text-align: center;">
        💡 <strong>Hint:</strong> The red ring is the same size and place as when you memorised the
        {st.session_state.memory_grid_size}×{st.session_state.memory_grid_size} grid.
    </div>
    """, unsafe_allow_html=True)

# Phase: Results
elif st.session_state.memory_phase == 'results':
    correct = st.session_state.memory_correct_count
    total = len(st.session_state.memory_questions)
    accuracy = correct / total if total > 0 else 0
    
    total_time = st.session_state.memory_end_time - st.session_state.memory_start_time
    
    # Calculate stars
    stars_earned = db.calculate_stars_for_accuracy(accuracy)
    
    # Header
    st.markdown('<p class="game-header">🎉 Amazing Job! 🎉</p>', unsafe_allow_html=True)
    
    # Stars
    star_icons = "⭐" * stars_earned
    st.markdown(f"""
    <div class="stars-earned">
        <p style="margin: 0;">You earned:</p>
        <p style="font-size: 4rem; margin: 0.5rem 0;">{star_icons}</p>
        <p style="font-size: 1.5rem; margin: 0;"><strong>{stars_earned}</strong> stars!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Encouragement
    if accuracy >= 0.8:
        message = "🌟 WOW! Your memory is SUPER strong! 🌟"
    elif accuracy >= 0.6:
        message = "🎉 Great job! You remembered a lot! 🎉"
    elif accuracy >= 0.4:
        message = "👍 Good try! Keep practicing! 👍"
    else:
        message = "💪 Nice effort! You'll do even better next time! 💪"
    
    st.markdown(f"""
    <div class="encouragement">
        {message}
    </div>
    """, unsafe_allow_html=True)
    
    # Score
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background: #E3F2FD; padding: 1.5rem; border-radius: 15px; text-align: center;">
            <p style="font-size: 1rem; margin: 0;">Correct</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #1565C0; margin: 0;">
                {correct}/{total}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: #FFF3E0; padding: 1.5rem; border-radius: 15px; text-align: center;">
            <p style="font-size: 1rem; margin: 0;">Score</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #FF6F00; margin: 0;">
                {accuracy * 100:.0f}%
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: #F3E5F5; padding: 1.5rem; border-radius: 15px; text-align: center;">
            <p style="font-size: 1rem; margin: 0;">Difficulty</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #7B1FA2; margin: 0;">
                {st.session_state.memory_difficulty.upper()}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show answers
    st.markdown("### Your Answers:")
    
    for i, answer in enumerate(st.session_state.memory_answers):
        icon = "✅" if answer['is_correct'] else "❌"
        color = "#C8E6C9" if answer['is_correct'] else "#FFCDD2"
        
        st.markdown(f"""
        <div style="background: {color}; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>{icon} Question {i+1}:</strong> {answer['question']}<br>
            Your answer: <strong>{answer['user_answer']}</strong>
            {'' if answer['is_correct'] else f" (Correct: {answer['correct_answer']})"}
        </div>
        """, unsafe_allow_html=True)
    
    # Save results
    db.record_visual_memory_result(
        user_id=user_id,
        grid_size=st.session_state.memory_grid_size,
        display_duration_seconds=st.session_state.memory_display_duration,
        total_questions=total,
        correct_answers=correct,
        accuracy=accuracy,
        time_spent_seconds=total_time,
        difficulty_level=st.session_state.memory_difficulty
    )
    
    db.record_session(
        user_id=user_id,
        module_name="visual_memory",
        accuracy=accuracy,
        time_spent_seconds=total_time,
        score=correct,
        max_score=total
    )
    
    # Award stars
    db.award_stars(
        user_id=user_id,
        module_name="visual_memory",
        stars=stars_earned,
        reason=f"Memory game ({st.session_state.memory_difficulty}) - {accuracy * 100:.0f}%"
    )
    
    # Navigation
    st.markdown("---")
    st.markdown("### What's next?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Play Again!", type="primary", use_container_width=True):
            st.session_state.memory_initialized = False
            st.rerun()
    
    with col2:
        if st.button("🎯 Focus Game", use_container_width=True):
            st.session_state.memory_initialized = False
            st.switch_page("pages/4_Attention_Focus.py")
    
    with col3:
        if st.button("🏠 Go Home", use_container_width=True):
            st.session_state.memory_initialized = False
            st.switch_page("app.py")
