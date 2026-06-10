"""
Attention & Focus Module - Child-Friendly, Fully Implemented

REAL IMPLEMENTATION with:
1. Age-based focus duration (min = age*2, max = age*3 minutes)
2. Large countdown timer with colorful display
3. Target letter finding task with big, colorful buttons
4. Positive reinforcement messages throughout
5. Stars awarded based on performance
6. Full accessibility features for dyslexia
"""

import streamlit as st
import sys
import os
import random
import string
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import SessionManager
from utils.theme import apply_theme, render_theme_toggle
from database.db_handler import DatabaseHandler

# Initialize session
SessionManager.initialize_session()
SessionManager.track_page_visit("attention_focus")

st.set_page_config(
    page_title="Focus Game!",
    page_icon="🎯",
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

.game-header { font-size: 2.5rem; color: #7B1FA2; text-align: center; margin-bottom: 1rem; }
.instruction-box, .how-to-play { color: #000000 !important; font-size: 1.35rem !important; line-height: 1.8 !important; }
.instruction-box strong, .instruction-box p, .instruction-box h3 { color: #000000 !important; }

.target-display {
    background: linear-gradient(135deg, #7B1FA2 0%, #9C27B0 100%);
    color: white;
    padding: 2rem;
    border-radius: 20px;
    text-align: center;
    margin: 1rem 0;
    box-shadow: 0 8px 25px rgba(123, 31, 162, 0.3);
}

.target-letter {
    font-size: 5rem;
    font-weight: bold;
    display: block;
    margin: 0.5rem 0;
}

.timer-display {
    font-size: 4rem;
    font-weight: bold;
    text-align: center;
    padding: 1.5rem;
    border-radius: 20px;
    margin: 1rem 0;
}

.timer-good {
    background: linear-gradient(135deg, #66BB6A 0%, #43A047 100%);
    color: white;
}

.timer-warning {
    background: linear-gradient(135deg, #FFA726 0%, #FB8C00 100%);
    color: white;
    animation: pulse 1s infinite;
}

.timer-danger {
    background: linear-gradient(135deg, #EF5350 0%, #E53935 100%);
    color: white;
    animation: pulse 0.5s infinite;
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.02); }
    100% { transform: scale(1); }
}

.score-card {
    background: linear-gradient(135deg, #42A5F5 0%, #1E88E5 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    font-size: 1.5rem;
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

.instruction-box {
    background: #FFF3E0;
    padding: 1.5rem;
    border-radius: 15px;
    border: 3px solid #FFB74D;
    font-size: 1.2rem;
    margin: 1rem 0;
}

.stars-earned {
    background: linear-gradient(135deg, #FFD54F 0%, #FFC107 100%);
    padding: 2rem;
    border-radius: 20px;
    text-align: center;
    font-size: 2rem;
    margin: 1rem 0;
}

.letter-btn {
    font-size: 1.8rem !important;
    padding: 1rem !important;
    margin: 0.3rem !important;
    min-height: 70px !important;
    border-radius: 12px !important;
}

/* Make Streamlit buttons bigger */
.stButton > button {
    font-size: 1.3rem;
    padding: 0.8rem 1.5rem;
    border-radius: 15px;
    font-family: 'OpenDyslexic', 'Comic Sans MS', sans-serif;
}

.result-correct {
    background: #C8E6C9 !important;
    border: 3px solid #4CAF50 !important;
}

.result-wrong {
    background: #FFCDD2 !important;
    border: 3px solid #F44336 !important;
}
</style>
""", unsafe_allow_html=True)


def initialize_attention_state():
    """Initialize or reset attention module state."""
    if 'attention_initialized' not in st.session_state:
        st.session_state.attention_initialized = False
    
    if not st.session_state.attention_initialized:
        st.session_state.attention_phase = 'setup'
        st.session_state.attention_target_letter = None
        st.session_state.attention_grid = []
        st.session_state.attention_grid_size = 6
        st.session_state.attention_target_count = 0
        st.session_state.attention_correct_clicks = 0
        st.session_state.attention_incorrect_clicks = 0
        st.session_state.attention_clicked_positions = set()
        st.session_state.attention_start_time = None
        st.session_state.attention_focus_duration = 0
        st.session_state.attention_time_remaining = 0
        st.session_state.attention_initialized = True


def generate_letter_grid(target_letter: str, grid_size: int, target_percentage: float = 0.15):
    """Generate a grid with target letters mixed among distractors."""
    total_cells = grid_size * grid_size
    num_targets = max(3, int(total_cells * target_percentage))
    
    # Use letters that are less confusing
    safe_distractors = [c for c in 'ACEFGHKLMNRSTUVWXYZ' if c != target_letter]
    
    grid = []
    target_positions = random.sample(range(total_cells), num_targets)
    
    for i in range(total_cells):
        if i in target_positions:
            grid.append(target_letter)
        else:
            grid.append(random.choice(safe_distractors))
    
    return grid, num_targets


def calculate_focus_duration(age: int, use_min: bool = True) -> int:
    """Calculate focus duration: min = age*2 minutes, max = age*3 minutes."""
    if use_min:
        return age * 2 * 60
    else:
        return age * 3 * 60


def get_encouragement_message():
    """Get a random encouraging message."""
    messages = [
        "You're doing great! 🌟",
        "Keep going! 💪",
        "Awesome! 🎉",
        "You found it! ⭐",
        "Super! 🚀",
        "Amazing! 🌈",
        "Wow! 🎯",
        "Perfect! ✨"
    ]
    return random.choice(messages)


# Initialize state
initialize_attention_state()

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
    render_theme_toggle(location="sidebar", key_suffix="att")
    st.divider()
    
    if st.button("🏠 Go Home", use_container_width=True):
        st.session_state.attention_initialized = False
        st.switch_page("app.py")
    
    if st.button("🎮 All Games", use_container_width=True):
        st.session_state.attention_initialized = False
        st.switch_page("pages/3_Learning_Support.py")

# Main content based on phase
if st.session_state.attention_phase == 'setup':
    st.markdown('<p class="game-header">🎯 Focus Game! 🎯</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="instruction-box">
        <h3>📋 How to Play:</h3>
        <p>1. Look at the <strong>TARGET LETTER</strong></p>
        <p>2. Find ALL the target letters in the grid</p>
        <p>3. Click on them as fast as you can!</p>
        <p>4. Earn stars! ⭐</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Settings
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⏱️ Game Time")
        
        min_focus = calculate_focus_duration(user_age, True) // 60
        max_focus = calculate_focus_duration(user_age, False) // 60
        
        st.info(f"Your age ({user_age}) means you can focus for {min_focus}-{max_focus} minutes!")
        
        duration_minutes = st.slider(
            "Choose game length (minutes)",
            min_value=1,
            max_value=max(5, max_focus),
            value=min(2, min_focus),
            help="Start with a short time!"
        )
    
    with col2:
        st.markdown("### 🔤 Grid Size")
        
        grid_size = st.select_slider(
            "How big should the grid be?",
            options=[4, 5, 6, 7, 8],
            value=5,
            format_func=lambda x: f"{x}x{x} ({'Easy' if x <= 5 else 'Medium' if x <= 6 else 'Hard'})"
        )
        
        st.info(f"Grid will have {grid_size * grid_size} letters!")
    
    # Target letter selection
    st.markdown("### 🎯 Target Letter")
    
    # Common confused letters for practice
    practice_letters = ['B', 'D', 'P', 'Q', 'M', 'N', 'W']
    target_letter = st.selectbox(
        "Pick a letter to find:",
        options=practice_letters + ['Random'],
        index=len(practice_letters),  # Default to Random
        help="Pick a letter you want to practice!"
    )
    
    if target_letter == 'Random':
        target_letter = random.choice(practice_letters)
    
    # Preview
    st.markdown(f"""
    <div class="target-display">
        <p>You will find this letter:</p>
        <span class="target-letter">{target_letter}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Start button
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 START GAME!", type="primary", use_container_width=True):
        grid, target_count = generate_letter_grid(target_letter, grid_size)
        
        st.session_state.attention_target_letter = target_letter
        st.session_state.attention_grid = grid
        st.session_state.attention_grid_size = grid_size
        st.session_state.attention_target_count = target_count
        st.session_state.attention_correct_clicks = 0
        st.session_state.attention_incorrect_clicks = 0
        st.session_state.attention_clicked_positions = set()
        st.session_state.attention_start_time = time.time()
        st.session_state.attention_focus_duration = duration_minutes * 60
        st.session_state.attention_time_remaining = duration_minutes * 60
        st.session_state.attention_phase = 'active'
        st.rerun()

elif st.session_state.attention_phase == 'active':
    # Calculate time
    elapsed = time.time() - st.session_state.attention_start_time
    time_remaining = max(0, st.session_state.attention_focus_duration - elapsed)
    
    # Check completion
    all_found = st.session_state.attention_correct_clicks >= st.session_state.attention_target_count
    time_up = time_remaining <= 0
    
    if time_up or all_found:
        st.session_state.attention_phase = 'completed'
        st.session_state.attention_time_remaining = time_remaining
        st.rerun()
    
    # Header row
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="target-display" style="padding: 1rem;">
            <p style="margin:0; font-size: 1rem;">Find this letter:</p>
            <span style="font-size: 3rem; font-weight: bold;">{st.session_state.attention_target_letter}</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Timer
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
        
        timer_class = 'timer-good'
        if time_remaining < 60:
            timer_class = 'timer-warning'
        if time_remaining < 15:
            timer_class = 'timer-danger'
        
        st.markdown(f"""
        <div class="timer-display {timer_class}">
            ⏱️ {minutes:02d}:{seconds:02d}
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="score-card">
            <p style="margin:0;">Found:</p>
            <p style="font-size: 2.5rem; margin:0; font-weight: bold;">
                {st.session_state.attention_correct_clicks}/{st.session_state.attention_target_count}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Grid
    st.markdown("---")
    st.markdown("### Click on all the target letters! 🎯")
    
    grid = st.session_state.attention_grid
    grid_size = st.session_state.attention_grid_size
    target = st.session_state.attention_target_letter
    clicked = st.session_state.attention_clicked_positions
    
    # Create grid with big buttons
    for row in range(grid_size):
        cols = st.columns(grid_size)
        for col in range(grid_size):
            idx = row * grid_size + col
            letter = grid[idx]
            
            with cols[col]:
                if idx in clicked:
                    if letter == target:
                        st.markdown(f"""
                        <div style="background: #C8E6C9; border: 3px solid #4CAF50;
                                    border-radius: 12px; padding: 0.8rem; text-align: center;
                                    font-size: 1.8rem; font-weight: bold; color: #2E7D32;
                                    min-height: 60px; display: flex; align-items: center;
                                    justify-content: center;">
                            ✓ {letter}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background: #FFCDD2; border: 3px solid #F44336;
                                    border-radius: 12px; padding: 0.8rem; text-align: center;
                                    font-size: 1.8rem; font-weight: bold; color: #C62828;
                                    min-height: 60px; display: flex; align-items: center;
                                    justify-content: center;">
                            ✗ {letter}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    if st.button(letter, key=f"letter_{idx}", use_container_width=True):
                        st.session_state.attention_clicked_positions.add(idx)
                        
                        if letter == target:
                            st.session_state.attention_correct_clicks += 1
                            st.toast(get_encouragement_message())
                        else:
                            st.session_state.attention_incorrect_clicks += 1
                        
                        st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏁 Finish Now", use_container_width=True):
            st.session_state.attention_phase = 'completed'
            st.session_state.attention_time_remaining = time_remaining
            st.rerun()
    
    with col2:
        st.write(f"Wrong clicks: {st.session_state.attention_incorrect_clicks}")
    
    # Auto-refresh
    time.sleep(0.5)
    st.rerun()

elif st.session_state.attention_phase == 'completed':
    # Calculate results
    correct = st.session_state.attention_correct_clicks
    incorrect = st.session_state.attention_incorrect_clicks
    total_targets = st.session_state.attention_target_count
    total_clicks = correct + incorrect
    
    if total_clicks > 0:
        click_accuracy = correct / total_clicks
    else:
        click_accuracy = 0
    
    completion_rate = correct / total_targets if total_targets > 0 else 0
    overall_accuracy = (click_accuracy * 0.7) + (completion_rate * 0.3)
    
    elapsed_time = st.session_state.attention_focus_duration - st.session_state.attention_time_remaining
    
    # Calculate stars
    stars_earned = db.calculate_stars_for_accuracy(overall_accuracy)
    
    # Header
    st.markdown('<p class="game-header">🎉 Great Job! 🎉</p>', unsafe_allow_html=True)
    
    # Stars display
    star_icons = "⭐" * stars_earned
    st.markdown(f"""
    <div class="stars-earned">
        <p style="margin: 0;">You earned:</p>
        <p style="font-size: 4rem; margin: 0.5rem 0;">{star_icons}</p>
        <p style="font-size: 1.5rem; margin: 0;"><strong>{stars_earned}</strong> stars!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Encouragement based on performance
    if overall_accuracy >= 0.8:
        message = "🌟 AMAZING! You're a focus superstar! 🌟"
    elif overall_accuracy >= 0.6:
        message = "🎉 Great job! You're getting better! 🎉"
    elif overall_accuracy >= 0.4:
        message = "👍 Good try! Keep practicing! 👍"
    else:
        message = "💪 Nice effort! You'll do even better next time! 💪"
    
    st.markdown(f"""
    <div class="encouragement">
        {message}
    </div>
    """, unsafe_allow_html=True)
    
    # Results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background: #E3F2FD; padding: 1.5rem; border-radius: 15px; text-align: center;">
            <p style="font-size: 1rem; margin: 0;">Letters Found</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #1565C0; margin: 0;">
                {correct}/{total_targets}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: #F3E5F5; padding: 1.5rem; border-radius: 15px; text-align: center;">
            <p style="font-size: 1rem; margin: 0;">Score</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #7B1FA2; margin: 0;">
                {overall_accuracy * 100:.0f}%
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: #E8F5E9; padding: 1.5rem; border-radius: 15px; text-align: center;">
            <p style="font-size: 1rem; margin: 0;">Time</p>
            <p style="font-size: 2.5rem; font-weight: bold; color: #388E3C; margin: 0;">
                {int(elapsed_time)}s
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Save results
    db.record_attention_result(
        user_id=user_id,
        target_letter=st.session_state.attention_target_letter,
        total_targets=total_targets,
        correct_clicks=correct,
        incorrect_clicks=incorrect,
        accuracy=overall_accuracy,
        time_spent_seconds=elapsed_time,
        focus_duration_target=st.session_state.attention_focus_duration // 60,
        completed_duration=int(elapsed_time),
        age_at_test=user_age
    )
    
    db.record_session(
        user_id=user_id,
        module_name="attention",
        accuracy=overall_accuracy,
        time_spent_seconds=elapsed_time,
        score=correct,
        max_score=total_targets
    )
    
    # Award stars
    db.award_stars(
        user_id=user_id,
        module_name="attention",
        stars=stars_earned,
        reason=f"Focus game - {overall_accuracy * 100:.0f}%"
    )
    
    # Navigation buttons
    st.markdown("---")
    st.markdown("### What's next?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Play Again!", type="primary", use_container_width=True):
            st.session_state.attention_initialized = False
            st.rerun()
    
    with col2:
        if st.button("🧩 Memory Game", use_container_width=True):
            st.session_state.attention_initialized = False
            st.switch_page("pages/5_Visual_Memory.py")
    
    with col3:
        if st.button("🏠 Go Home", use_container_width=True):
            st.session_state.attention_initialized = False
            st.switch_page("app.py")
