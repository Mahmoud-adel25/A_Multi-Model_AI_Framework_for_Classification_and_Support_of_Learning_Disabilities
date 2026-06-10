"""
Upload Handwriting Page - Child-Friendly Design

Upload handwriting images for AI classification.
Errors shown with st.exception() - no silent failures.
"""

import streamlit as st
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import SessionManager
from utils.image_processing import ImageProcessor
from utils.logger import get_logger, log_classification, log_error
from utils.theme import apply_theme, render_theme_toggle
from models.model_loader import ModelLoader

logger = get_logger("upload")

# Initialize session
SessionManager.initialize_session()
SessionManager.track_page_visit("upload_handwriting")

st.set_page_config(
    page_title="Check My Writing",
    page_icon="📝",
    layout="wide"
)
apply_theme()

# Child-friendly CSS: instructional text BLACK, high contrast
st.markdown("""
<style>
@import url('https://fonts.cdnfonts.com/css/opendyslexic');
.stApp { font-family: 'OpenDyslexic', 'Comic Sans MS', sans-serif; }
.child-title { font-size: 2.5rem; color: #1565C0; text-align: center; margin-bottom: 1rem; }
.instruction-box {
    background: #FFFFFF;
    color: #000000 !important;
    padding: 1.5rem;
    border-radius: 15px;
    border: 3px solid #333333;
    font-size: 1.35rem;
    line-height: 1.8;
    margin: 1rem 0;
}
.instruction-box strong, .instruction-box p { color: #000000 !important; }
.success-message {
    background: #C8E6C9;
    color: #000000 !important;
    padding: 1.5rem;
    border-radius: 15px;
    border: 3px solid #2E7D32;
    text-align: center;
    font-size: 1.3rem;
}
.encouragement {
    background: #FFF9C4;
    color: #000000 !important;
    padding: 1.5rem;
    border-radius: 15px;
    border: 3px solid #F9A825;
    text-align: center;
    font-size: 1.5rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# Initialize model loader (fresh each time to avoid stale cache)
def get_model_loader():
    return ModelLoader()

model_loader = get_model_loader()

# Check mode
is_child_mode = st.session_state.get('app_mode', 'child') == 'child'

# Title
if is_child_mode:
    st.markdown('<p class="child-title">📝 Check My Writing! 📝</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="instruction-box">
        <strong>📸 How to use:</strong><br>
        1. Take a picture of your writing<br>
        2. Upload it here<br>
        3. Click the button to check!
    </div>
    """, unsafe_allow_html=True)
else:
    st.title("📝 Upload Handwriting Sample")
    st.markdown("Upload a handwriting image for AI analysis and classification.")

# Sidebar
with st.sidebar:
    if is_child_mode:
        st.markdown("### 🏠 Go Back")
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")
        st.divider()
        from database.db_handler import DatabaseHandler
        db = DatabaseHandler()
        total_stars = db.get_total_stars(SessionManager.get_user_id())
        st.markdown(f"### ⭐ My Stars: {total_stars}")
    else:
        st.markdown("### Navigation")
        if st.button("Back to Dashboard"):
            st.switch_page("app.py")

    st.divider()
    st.markdown("### 🎨 Appearance")
    render_theme_toggle(location="sidebar", key_suffix="upload")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📤 Upload Your Writing" if is_child_mode else "Upload Image")
    
    uploaded_file = st.file_uploader(
        "Choose a picture of your writing" if is_child_mode else "Choose a handwriting image",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'],
        help="Pick a clear picture of your writing!"
    )
    
    if uploaded_file is not None:
        image = ImageProcessor.load_image(uploaded_file)
        
        if image:
            is_valid, message = ImageProcessor.validate_image(image)
            
            if is_valid:
                SessionManager.set_current_image(image)
                
                if is_child_mode:
                    st.markdown('<div class="success-message">✅ Great! Your picture is ready!</div>', unsafe_allow_html=True)
                else:
                    info = ImageProcessor.get_image_info(image)
                    st.success(f"Image loaded! Size: {info['width']} x {info['height']}")
                
                display_image = ImageProcessor.preprocess_for_display(image)
                st.image(display_image, caption="Your Writing", use_container_width=True)
            else:
                st.error("Oops! Try a different picture." if is_child_mode else message)

with col2:
    if is_child_mode:
        selected_model = "efficientnet"
        st.markdown("### 🔍 Check Your Writing")
        st.markdown('<div class="instruction-box">Click the big button below to check your writing!</div>', unsafe_allow_html=True)
    else:
        st.subheader("Model Selection")
        st.caption("Trained on handwriting samples. Best results with clear, well-lit photos. Use as a support tool, not a diagnosis.")
        with st.expander("About classification"):
            st.caption(
                "Classification can differ on reversed or transformed versions of the same handwriting. "
                "Models use visual features (orientation, stroke direction, layout) that can vary with transformation "
                "rather than transformation-invariant dyslexia-related patterns."
            )
        weights_status = model_loader.check_weights_available()
        
        model_options = {
            "efficientnet": "EfficientNet-B0",
            "mobilenet": "MobileNet V3 Large",
            "cnn": "Custom CNN (28x28 input)",
        }
        
        selected_model = st.selectbox(
            "Select Classification Model",
            options=list(model_options.keys()),
            format_func=lambda x: model_options[x],
            index=0,
        )
        st.write("**Model Weights Status:**")
        for model_name, available in weights_status.items():
            status = "✅ Ready" if available else "⚠️ Not found"
            st.write(f"- {model_options[model_name]}: {status}")
        
        st.write(f"**Device:** {model_loader.get_device()}")
    
    # Analyze button
    button_label = "🔍 Check My Writing!" if is_child_mode else "Classify Handwriting"
    
    if st.button(button_label, type="primary", 
                 disabled=SessionManager.get_current_image() is None,
                 use_container_width=True):
        
        current_image = SessionManager.get_current_image()
        
        if current_image:
            with st.spinner("Looking at your writing..." if is_child_mode else "Classifying..."):
                try:
                    if not model_loader.is_model_loaded(selected_model):
                        model_loader.load_model(selected_model)
                    
                    result = model_loader.predict(current_image, selected_model)
                except Exception as e:
                    traceback.print_exc()
                    log_error(logger, "classification", e)
                    st.error("Classification failed. See error details below.")
                    st.exception(e)
                    result = None
                
                if result is not None and "error" in result:
                    st.error(result["error"])
                elif result is not None:
                    debug = result.get("debug_info", {})
                    log_classification(
                        logger,
                        result["model_used"],
                        debug.get("input_shape", ()),
                        result["predicted_class"],
                        result["predicted_label"],
                        result["confidence"],
                    )
                    
                    SessionManager.set_classification_result(result)
                    
                    from database.db_handler import DatabaseHandler
                    db = DatabaseHandler()
                    db.record_classification(
                        user_id=SessionManager.get_user_id(),
                        model_used=result["model_used"],
                        predicted_class=result["predicted_class"],
                        predicted_label=result["predicted_label"],
                        confidence=result["confidence"],
                        probabilities=result["probabilities"],
                        image_filename=uploaded_file.name if uploaded_file else None,
                    )
                    db.award_stars(
                        user_id=SessionManager.get_user_id(),
                        module_name="writing_check",
                        stars=1,
                        reason="Checked writing",
                    )
                    
                    if is_child_mode:
                        st.balloons()
                        st.markdown('<div class="encouragement">🌟 Great job uploading your writing! 🌟<br>You earned a star! ⭐</div>', unsafe_allow_html=True)
                        st.markdown('<div class="success-message"><h3>Keep practicing!</h3><p>Every time you write, you get better! 📝</p></div>', unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🎯 Play Focus Game", use_container_width=True):
                                st.switch_page("pages/4_Attention_Focus.py")
                        with col2:
                            if st.button("🧩 Play Memory Game", use_container_width=True):
                                st.switch_page("pages/5_Visual_Memory.py")
                    else:
                        st.success("Classification complete!")
                        conf = result["confidence"]
                        if conf < 0.65:
                            st.warning("Result is uncertain (low confidence). Try a clearer or better-lit photo for a more reliable result.")
                        if result.get("model_note"):
                            st.info(result["model_note"])
                        st.write(f"**Prediction:** {result['predicted_label']}")
                        st.write(f"**Confidence:** {result['confidence'] * 100:.2f}%")
                        st.write("**Probabilities:**")
                        for label, prob in result['probabilities'].items():
                            st.progress(prob, text=f"{label}: {prob*100:.1f}%")
                        if st.button("View Detailed Results"):
                            st.switch_page("pages/2_Classification_Result.py")
                    
                    # Debug panel (expandable)
                    debug_info = result.get("debug_info", {})
                    if debug_info and not is_child_mode:
                        with st.expander("Debug info"):
                            st.write("Input tensor shape:", debug_info.get("input_shape"))
                            st.write("Output tensor shape:", debug_info.get("output_shape"))
                            st.write("Predicted class index:", debug_info.get("predicted_class_index"))
                            st.write("Device:", debug_info.get("device"))

# Bottom navigation
if is_child_mode:
    st.divider()
    st.markdown("### 🎮 More Activities")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏠 Go Home", use_container_width=True, key="home_btn"):
            st.switch_page("app.py")
    with col2:
        if st.button("🎯 Focus Game", use_container_width=True, key="focus_btn"):
            st.switch_page("pages/4_Attention_Focus.py")
    with col3:
        if st.button("🧩 Memory Game", use_container_width=True, key="memory_btn"):
            st.switch_page("pages/5_Visual_Memory.py")
