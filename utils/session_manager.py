"""
Session Manager for Learning Disability Detection System

This module manages user sessions and state in the Streamlit application.
It handles user identification, session data, and state persistence.
"""

import streamlit as st
import uuid
from datetime import datetime
from typing import Any, Optional, Dict


class SessionManager:
    """
    Manages Streamlit session state for the application.
    
    Handles:
    - User session initialization
    - State persistence across pages
    - Temporary data storage
    - Session cleanup
    """
    
    # Session state keys
    USER_ID_KEY = "user_id"
    USER_NAME_KEY = "user_name"
    USER_AGE_KEY = "user_age"
    CURRENT_IMAGE_KEY = "current_image"
    CLASSIFICATION_RESULT_KEY = "classification_result"
    ATTENTION_STATE_KEY = "attention_state"
    MEMORY_STATE_KEY = "memory_state"
    
    @staticmethod
    def initialize_session():
        """
        Initialize session state with default values.
        Call this at the start of the application.
        """
        # Generate or retrieve user ID
        if SessionManager.USER_ID_KEY not in st.session_state:
            st.session_state[SessionManager.USER_ID_KEY] = str(uuid.uuid4())[:8]
        
        # Initialize other session variables
        defaults = {
            SessionManager.USER_NAME_KEY: None,
            SessionManager.USER_AGE_KEY: None,
            SessionManager.CURRENT_IMAGE_KEY: None,
            SessionManager.CLASSIFICATION_RESULT_KEY: None,
            SessionManager.ATTENTION_STATE_KEY: {},
            SessionManager.MEMORY_STATE_KEY: {},
            "session_start": datetime.now(),
            "page_visits": {},
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @staticmethod
    def get_user_id() -> str:
        """Get the current user's session ID."""
        if SessionManager.USER_ID_KEY not in st.session_state:
            SessionManager.initialize_session()
        return st.session_state[SessionManager.USER_ID_KEY]
    
    @staticmethod
    def set_user_id(user_id: str):
        """Set a custom user ID."""
        st.session_state[SessionManager.USER_ID_KEY] = user_id
    
    @staticmethod
    def get_user_name() -> Optional[str]:
        """Get the current user's name."""
        return st.session_state.get(SessionManager.USER_NAME_KEY)
    
    @staticmethod
    def set_user_name(name: str):
        """Set the current user's name."""
        st.session_state[SessionManager.USER_NAME_KEY] = name
    
    @staticmethod
    def get_user_age() -> Optional[int]:
        """Get the current user's age."""
        return st.session_state.get(SessionManager.USER_AGE_KEY)
    
    @staticmethod
    def set_user_age(age: int):
        """Set the current user's age."""
        st.session_state[SessionManager.USER_AGE_KEY] = age
    
    @staticmethod
    def get_current_image():
        """Get the currently uploaded image."""
        return st.session_state.get(SessionManager.CURRENT_IMAGE_KEY)
    
    @staticmethod
    def set_current_image(image):
        """Set the currently uploaded image."""
        st.session_state[SessionManager.CURRENT_IMAGE_KEY] = image
    
    @staticmethod
    def get_classification_result() -> Optional[Dict]:
        """Get the current classification result."""
        return st.session_state.get(SessionManager.CLASSIFICATION_RESULT_KEY)
    
    @staticmethod
    def set_classification_result(result: Dict):
        """Set the current classification result."""
        st.session_state[SessionManager.CLASSIFICATION_RESULT_KEY] = result
    
    @staticmethod
    def get_attention_state() -> Dict:
        """Get the attention module state."""
        return st.session_state.get(SessionManager.ATTENTION_STATE_KEY, {})
    
    @staticmethod
    def set_attention_state(state: Dict):
        """Set the attention module state."""
        st.session_state[SessionManager.ATTENTION_STATE_KEY] = state
    
    @staticmethod
    def update_attention_state(key: str, value: Any):
        """Update a specific key in attention state."""
        if SessionManager.ATTENTION_STATE_KEY not in st.session_state:
            st.session_state[SessionManager.ATTENTION_STATE_KEY] = {}
        st.session_state[SessionManager.ATTENTION_STATE_KEY][key] = value
    
    @staticmethod
    def get_memory_state() -> Dict:
        """Get the visual memory module state."""
        return st.session_state.get(SessionManager.MEMORY_STATE_KEY, {})
    
    @staticmethod
    def set_memory_state(state: Dict):
        """Set the visual memory module state."""
        st.session_state[SessionManager.MEMORY_STATE_KEY] = state
    
    @staticmethod
    def update_memory_state(key: str, value: Any):
        """Update a specific key in memory state."""
        if SessionManager.MEMORY_STATE_KEY not in st.session_state:
            st.session_state[SessionManager.MEMORY_STATE_KEY] = {}
        st.session_state[SessionManager.MEMORY_STATE_KEY][key] = value
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get a value from session state."""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set(key: str, value: Any):
        """Set a value in session state."""
        st.session_state[key] = value
    
    @staticmethod
    def delete(key: str):
        """Delete a key from session state."""
        if key in st.session_state:
            del st.session_state[key]
    
    @staticmethod
    def clear_classification_data():
        """Clear classification-related data."""
        st.session_state[SessionManager.CURRENT_IMAGE_KEY] = None
        st.session_state[SessionManager.CLASSIFICATION_RESULT_KEY] = None
    
    @staticmethod
    def clear_attention_state():
        """Clear attention module state."""
        st.session_state[SessionManager.ATTENTION_STATE_KEY] = {}
    
    @staticmethod
    def clear_memory_state():
        """Clear visual memory module state."""
        st.session_state[SessionManager.MEMORY_STATE_KEY] = {}
    
    @staticmethod
    def track_page_visit(page_name: str):
        """Track a page visit."""
        if "page_visits" not in st.session_state:
            st.session_state["page_visits"] = {}
        
        if page_name not in st.session_state["page_visits"]:
            st.session_state["page_visits"][page_name] = 0
        
        st.session_state["page_visits"][page_name] += 1
    
    @staticmethod
    def get_session_duration() -> float:
        """Get session duration in seconds."""
        start = st.session_state.get("session_start", datetime.now())
        return (datetime.now() - start).total_seconds()
    
    @staticmethod
    def reset_session():
        """Reset the entire session to default state."""
        # Preserve user ID
        user_id = st.session_state.get(SessionManager.USER_ID_KEY)
        
        # Clear all state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Re-initialize with preserved user ID
        st.session_state[SessionManager.USER_ID_KEY] = user_id or str(uuid.uuid4())[:8]
        SessionManager.initialize_session()
