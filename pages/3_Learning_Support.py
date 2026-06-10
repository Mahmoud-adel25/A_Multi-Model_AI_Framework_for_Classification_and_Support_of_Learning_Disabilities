"""
Learning Support Layer - Child-Friendly Hub

Central hub for accessing learning support modules.
Colorful, accessible design for children with learning disabilities.
"""

import streamlit as st
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import SessionManager
from utils.theme import apply_theme, render_theme_toggle
from database.db_handler import DatabaseHandler

# Initialize session
SessionManager.initialize_session()
SessionManager.track_page_visit("learning_support")

st.set_page_config(
    page_title="Let's Practice!",
    page_icon="🎮",
    layout="wide"
)
apply_theme()

# Child-friendly CSS
st.markdown("""
<style>
@import url('https://fonts.cdnfonts.com/css/opendyslexic');
.stApp { 
    font-family: 'OpenDyslexic', 'Comic Sans MS', sans-serif;
    line-height: 1.8;
}
.fun-header { font-size: 3rem; color: #1565C0; text-align: center; margin-bottom: 0.5rem; }
.instruction-text, .how-to-play, .level-text {
    color: #000000 !important;
    font-size: 1.35rem !important;
    line-height: 1.8 !important;
}
.stars-banner {
    background: linear-gradient(135deg, #FFD54F 0%, #FFC107 100%);
    padding: 1rem 2rem;
    border-radius: 20px;
    text-align: center;
    font-size: 1.5rem;
    color: #5D4037;
    margin: 1rem auto;
    max-width: 400px;
    box-shadow: 0 4px 15px rgba(255,193,7,0.3);
}
.game-card {
    background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
    padding: 2rem;
    border-radius: 20px;
    text-align: center;
    margin: 1rem 0;
    border: 4px solid #42A5F5;
    transition: transform 0.2s;
}
.game-card:hover {
    transform: scale(1.02);
}
.game-card-purple {
    background: linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%);
    border-color: #AB47BC;
}
.game-card-orange {
    background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
    border-color: #FF9800;
}
.game-icon {
    font-size: 4rem;
    display: block;
    margin-bottom: 0.5rem;
}
.game-title {
    font-size: 1.8rem;
    font-weight: bold;
    color: #1565C0;
    margin-bottom: 0.5rem;
}
.game-desc {
    font-size: 1.1rem;
    color: #424242;
}
.encouragement {
    background: linear-gradient(135deg, #C8E6C9 0%, #A5D6A7 100%);
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    font-size: 1.5rem;
    color: #2E7D32;
    margin: 1.5rem 0;
    border: 3px solid #66BB6A;
}
.progress-box {
    background: #ECEFF1;
    padding: 1rem;
    border-radius: 15px;
    text-align: center;
    margin: 0.5rem;
}
.progress-number {
    font-size: 2rem;
    font-weight: bold;
    color: #1565C0;
}
</style>
""", unsafe_allow_html=True)

# Get user info
user_id = SessionManager.get_user_id()
user_age = SessionManager.get_user_age() or 8
user_name = SessionManager.get_user_name() or "Friend"

db = DatabaseHandler()
total_stars = db.get_total_stars(user_id)

# Check mode
is_child_mode = st.session_state.get('app_mode', 'child') == 'child'

# Header
st.markdown('<p class="fun-header">🎮 Let\'s Practice! 🎮</p>', unsafe_allow_html=True)

# Stars banner
st.markdown(f"""
<div class="stars-banner">
    ⭐ You have <strong>{total_stars}</strong> stars! ⭐
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown(f"### 👋 Hi, {user_name}!")
    st.markdown(f"**Age:** {user_age} years")
    
    st.divider()
    
    # Progress summary
    st.markdown("### 📊 My Progress")
    
    attention_history = db.get_attention_history(user_id, limit=100)
    memory_history = db.get_visual_memory_history(user_id, limit=100)
    
    st.markdown(f"**Focus Games:** {len(attention_history)}")
    st.markdown(f"**Memory Games:** {len(memory_history)}")
    st.markdown(f"**Total Stars:** ⭐ {total_stars}")
    
    st.divider()

    st.markdown("### 🎨 Appearance")
    render_theme_toggle(location="sidebar", key_suffix="ls")

    st.divider()
    if st.button("🏠 Go Home", use_container_width=True):
        st.switch_page("app.py")

# Encouragement
encouragements = [
    f"You're doing amazing, {user_name}! 🌟",
    "Every game makes your brain stronger! 💪",
    "You're a superstar learner! ⭐",
    "Let's have fun and learn! 🎉",
    "You can do anything! 🚀",
    "Practice makes perfect! Keep going! 🎯"
]

st.markdown(f"""
<div class="encouragement">
    {random.choice(encouragements)}
</div>
""", unsafe_allow_html=True)

# Game cards
st.markdown("### Choose a Game!")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="game-card game-card-purple">
        <span class="game-icon">🎯</span>
        <p class="game-title">Focus Game</p>
        <p class="game-desc">Find the letters and train your focus!</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🎯 Play Focus Game!", use_container_width=True, key="btn_attention"):
        st.switch_page("pages/4_Attention_Focus.py")
    
    # Show stats
    if attention_history:
        latest = attention_history[0]
        avg_acc = sum(h.get('accuracy', 0) for h in attention_history) / len(attention_history)
        st.markdown(f"""
        <div class="progress-box">
            <span class="progress-number">{len(attention_history)}</span><br>
            Games Played<br>
            Best: {max(h.get('accuracy', 0) for h in attention_history) * 100:.0f}%
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="game-card game-card-orange">
        <span class="game-icon">🧩</span>
        <p class="game-title">Memory Game</p>
        <p class="game-desc">Remember the letters and boost your memory!</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🧩 Play Memory Game!", use_container_width=True, key="btn_memory"):
        st.switch_page("pages/5_Visual_Memory.py")
    
    # Show stats
    if memory_history:
        st.markdown(f"""
        <div class="progress-box">
            <span class="progress-number">{len(memory_history)}</span><br>
            Games Played<br>
            Best: {max(h.get('accuracy', 0) for h in memory_history) * 100:.0f}%
        </div>
        """, unsafe_allow_html=True)

# More games row
st.divider()
st.markdown("### 🎮 More Games to Try!")

col3, col4, col5 = st.columns(3)

with col3:
    if st.button("🔊 Sound Memory", use_container_width=True, key="btn_auditory"):
        st.switch_page("pages/6_Auditory_Memory.py")

with col4:
    if st.button("🔢 Number Memory", use_container_width=True, key="btn_working"):
        st.switch_page("pages/7_Working_Memory.py")

with col5:
    if st.button("⚡ Quick Think", use_container_width=True, key="btn_processing"):
        st.switch_page("pages/8_Processing_Speed.py")

st.divider()

# Final assessment button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🏆 Take the Final Challenge!", use_container_width=True, type="primary", key="btn_final"):
        st.switch_page("pages/9_Final_Assessment.py")

# Focus duration info for children
st.divider()

min_focus = user_age * 2
max_focus = user_age * 3

st.markdown(f"""
<div style="background: #E8F5E9; padding: 1.5rem; border-radius: 15px; 
            border: 3px solid #81C784; text-align: center;">
    <h3 style="color: #2E7D32; margin: 0;">💡 Did you know?</h3>
    <p style="font-size: 1.2rem; color: #424242; margin: 0.5rem 0 0 0;">
        At your age, your brain can focus for <strong>{min_focus}-{max_focus} minutes</strong>!<br>
        That's perfect for our games! 🧠
    </p>
</div>
""", unsafe_allow_html=True)

# Tips section
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 💡 Tips for Success")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="background: #F3E5F5; padding: 1rem; border-radius: 15px; color: #000000;">
        <strong>🎯 Focus Game Tips:</strong><br>
        • Look carefully at each letter<br>
        • Take your time<br>
        • Don't worry about mistakes!
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: #FFF3E0; padding: 1rem; border-radius: 15px; color: #000000;">
        <strong>🧩 Memory Game Tips:</strong><br>
        • Look at the whole grid first<br>
        • Say the letters in your head<br>
        • It's okay to guess!
    </div>
    """, unsafe_allow_html=True)

# Recent activity
if attention_history or memory_history:
    st.divider()
    st.markdown("### 🎉 Recent Games")
    
    recent = []
    for h in attention_history[:3]:
        recent.append(("🎯 Focus", h.get('accuracy', 0), h.get('created_at')))
    for h in memory_history[:3]:
        recent.append(("🧩 Memory", h.get('accuracy', 0), h.get('created_at')))
    
    recent.sort(key=lambda x: x[2] if x[2] else "", reverse=True)
    
    for game, acc, date in recent[:5]:
        stars = "⭐" * db.calculate_stars_for_accuracy(acc)
        st.markdown(f"**{game}** - {acc * 100:.0f}% - {stars}")
