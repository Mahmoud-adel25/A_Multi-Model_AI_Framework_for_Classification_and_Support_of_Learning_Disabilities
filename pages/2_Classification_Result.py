"""
Classification Result Page

In Child Mode: Shows encouraging feedback only (no medical labels)
In Teacher Mode: Shows actual classification results
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import SessionManager
from utils.image_processing import ImageProcessor
from utils.theme import apply_theme, render_theme_toggle
from database.db_handler import DatabaseHandler

# Initialize session
SessionManager.initialize_session()
SessionManager.track_page_visit("classification_result")

st.set_page_config(
    page_title="Results",
    page_icon="📊",
    layout="wide"
)
apply_theme()

with st.sidebar:
    st.markdown("### 🎨 Appearance")
    render_theme_toggle(location="sidebar", key_suffix="results")

# Check mode
is_child_mode = st.session_state.get('app_mode', 'child') == 'child'

# Child-friendly CSS
if is_child_mode:
    st.markdown("""
    <style>
    @import url('https://fonts.cdnfonts.com/css/opendyslexic');
    .stApp { font-family: 'OpenDyslexic', 'Comic Sans MS', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

result = SessionManager.get_classification_result()
current_image = SessionManager.get_current_image()

if is_child_mode:
    # Child mode - only show encouraging feedback
    st.markdown("""
    <h1 style="text-align: center; color: #1565C0;">🌟 Great Job! 🌟</h1>
    """, unsafe_allow_html=True)
    
    if current_image:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            display_image = ImageProcessor.preprocess_for_display(current_image)
            st.image(display_image, caption="Your Writing", use_container_width=True)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #C8E6C9 0%, #A5D6A7 100%);
                padding: 2rem; border-radius: 15px; text-align: center; margin: 1rem 0;">
        <h2 style="color: #2E7D32; margin: 0;">Thanks for sharing your writing! 📝</h2>
        <p style="font-size: 1.3rem; margin: 1rem 0 0 0;">
            Keep practicing! Every time you write, you get better! 💪
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #E3F2FD; padding: 1.5rem; border-radius: 15px; text-align: center;">
        <h3 style="color: #1565C0;">Want to improve your skills?</h3>
        <p>Try our fun practice games!</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 Focus Game", use_container_width=True):
            st.switch_page("pages/4_Attention_Focus.py")
    
    with col2:
        if st.button("🧩 Memory Game", use_container_width=True):
            st.switch_page("pages/5_Visual_Memory.py")
    
    with col3:
        if st.button("🏠 Go Home", use_container_width=True):
            st.switch_page("app.py")

else:
    # Teacher mode - show actual results
    st.title("📊 Classification Results")
    
    if result and current_image:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Analyzed Image")
            display_image = ImageProcessor.preprocess_for_display(current_image)
            st.image(display_image, caption="Classified Image", use_container_width=True)
            st.write(f"**Model Used:** {result['model_used'].upper()}")
            if result.get("model_note"):
                st.info(result["model_note"])
        
        with col2:
            st.subheader("Prediction Result")
            
            predicted_label = result['predicted_label']
            confidence = result['confidence']
            
            if confidence < 0.65:
                st.warning("Result is uncertain (low confidence). Try a clearer or better-lit photo for a more reliable result.")
            
            # Binary: Non-Dyslexic (green) or Dyslexic (amber)
            if predicted_label == "Non-Dyslexic":
                color = "#28a745"
            else:
                color = "#f0ad4e"
            
            st.markdown(f"""
            <div style="background: {color}20; padding: 2rem; border-radius: 10px; 
                        border-left: 5px solid {color}; margin-bottom: 1rem;">
                <h2 style="color: {color}; margin: 0;">{predicted_label}</h2>
                <p style="font-size: 1.5rem; margin: 0.5rem 0 0 0;">
                    Confidence: <strong>{confidence * 100:.2f}%</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Probability breakdown
            st.subheader("Probability Distribution")
            probabilities = result.get('probabilities', {})
            
            for class_name, prob in probabilities.items():
                st.write(f"**{class_name}**")
                st.progress(prob, text=f"{prob * 100:.2f}%")
            
            # Recommendations (binary: Dyslexic vs Non-Dyslexic only)
            st.divider()
            st.subheader("Recommendations")
            
            if predicted_label == "Non-Dyslexic":
                st.success("Handwriting pattern appears typical. Continue regular practice.")
            else:
                st.warning("""
                Patterns may suggest further assessment. Recommendations:
                - Use the Attention & Focus and Visual Memory modules for practice
                - Multi-sensory learning approaches
                - Consult with an educational specialist if needed
                - Track progress over time
                """)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Upload New Image"):
                SessionManager.clear_classification_data()
                st.switch_page("pages/1_Upload_Handwriting.py")
        
        with col2:
            if st.button("Back to Dashboard"):
                st.switch_page("app.py")
    
    else:
        st.info("No classification result available.")
        if st.button("Go to Upload Page"):
            st.switch_page("pages/1_Upload_Handwriting.py")
    
    # History section (Teacher only)
    st.divider()
    st.subheader("Classification History")
    
    db = DatabaseHandler()
    user_id = SessionManager.get_user_id()
    history = db.get_classification_history(user_id, limit=10)
    
    if history:
        for i, record in enumerate(history):
            with st.expander(f"#{i+1} - {record['predicted_label']} ({record['created_at']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Model:** {record['model_used']}")
                    st.write(f"**Prediction:** {record['predicted_label']}")
                    st.write(f"**Confidence:** {record['confidence'] * 100:.2f}%")
                with col2:
                    probs = record.get('probabilities', {})
                    st.write("**Probabilities:**")
                    for name, prob in probs.items():
                        st.write(f"- {name}: {prob * 100:.2f}%")
    else:
        st.write("No classification history yet.")
