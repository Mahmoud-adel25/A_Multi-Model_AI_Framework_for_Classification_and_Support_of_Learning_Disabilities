"""
Database Handler for Learning Disability Detection System

Persistent SQLite on disk. NO DROP TABLE, NO DELETE FROM on startup.
Only CREATE TABLE IF NOT EXISTS. One parent -> many children.
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

# Persistent DB file on disk - never wiped on rerun
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "learning_support.db")

def _get_db_logger():
    try:
        from utils.logger import get_logger
        return get_logger("learning_support.db")
    except Exception:
        return logging.getLogger("learning_support.db")

_db_logger = _get_db_logger()


class DatabaseHandler:
    """
    SQLite database handler for tracking user progress and assessment results.
    
    Provides methods for:
    - Creating and managing user sessions
    - Storing classification results
    - Recording attention module performance
    - Recording visual memory module performance
    - Retrieving progress reports
    """
    
    def __init__(self, db_path: str = DB_PATH):
        """
        Initialize the database handler.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory for dict-like access."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Create tables only if they do NOT exist. No DROP, no DELETE."""
        db_existed = os.path.exists(self.db_path)
        conn = self._get_connection()
        cursor = conn.cursor()

        if db_existed:
            _db_logger.info("Database file found; reusing existing DB: %s", self.db_path)
        else:
            _db_logger.info("Database file created: %s", self.db_path)

        # Parents: one parent -> many children
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parents (
                parent_id TEXT PRIMARY KEY,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO parents (parent_id, name) VALUES (?, ?)", ("default", "Default Parent"))

        # Users (children) - optional parent_id for multi-child support
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                parent_id TEXT DEFAULT 'default',
                name TEXT,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES parents(parent_id)
            )
        """)
        # Add parent_id if table already existed without it
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if "parent_id" not in columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN parent_id TEXT DEFAULT 'default'")
                conn.commit()
            except sqlite3.OperationalError:
                pass
        
        # Sessions table - tracks each assessment session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                module_name TEXT NOT NULL,
                accuracy REAL,
                time_spent_seconds REAL,
                score INTEGER,
                max_score INTEGER,
                additional_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Classification results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classification_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                model_used TEXT NOT NULL,
                predicted_class INTEGER,
                predicted_label TEXT,
                confidence REAL,
                probabilities TEXT,
                image_filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Attention module results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attention_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                target_letter TEXT,
                total_targets INTEGER,
                correct_clicks INTEGER,
                incorrect_clicks INTEGER,
                accuracy REAL,
                time_spent_seconds REAL,
                focus_duration_target INTEGER,
                completed_duration INTEGER,
                age_at_test INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Visual memory results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visual_memory_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                grid_size INTEGER,
                display_duration_seconds REAL,
                total_questions INTEGER,
                correct_answers INTEGER,
                accuracy REAL,
                time_spent_seconds REAL,
                difficulty_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Auditory memory results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auditory_memory_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                sequence_length INTEGER,
                total_rounds INTEGER,
                correct_rounds INTEGER,
                accuracy REAL,
                time_spent_seconds REAL,
                difficulty_level TEXT,
                max_span_reached INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Working memory (digit-span) results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS working_memory_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                mode TEXT,
                span_length INTEGER,
                total_trials INTEGER,
                correct_trials INTEGER,
                accuracy REAL,
                time_spent_seconds REAL,
                max_span_reached INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Processing speed results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_speed_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                task_type TEXT,
                total_trials INTEGER,
                correct_trials INTEGER,
                accuracy REAL,
                avg_reaction_ms REAL,
                time_spent_seconds REAL,
                difficulty_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Final assessment results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS final_assessment_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                overall_score REAL,
                attention_score REAL,
                visual_memory_score REAL,
                auditory_memory_score REAL,
                working_memory_score REAL,
                processing_speed_score REAL,
                time_spent_seconds REAL,
                age_at_test INTEGER,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Stars/Gamification table - tracks earned stars
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stars (
                star_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                module_name TEXT NOT NULL,
                stars_earned INTEGER DEFAULT 0,
                reason TEXT,
                session_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
        conn.close()
        _db_logger.info("DB init complete (CREATE TABLE IF NOT EXISTS only)")

    # ==================== User Management ====================

    def get_user_by_name(self, name: str, parent_id: str = "default") -> Optional[Dict[str, Any]]:
        """Find existing child by name (and parent). For login - do not create new."""
        if not name or not name.strip():
            return None
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE TRIM(LOWER(name)) = TRIM(LOWER(?)) AND parent_id = ? LIMIT 1",
            (name.strip(), parent_id),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_children_for_parent(self, parent_id: str = "default") -> List[Dict[str, Any]]:
        """List all children for a parent."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE parent_id = ? ORDER BY last_active DESC",
            (parent_id,),
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def create_or_get_user(self, user_id: str, name: str = None, age: int = None, parent_id: str = "default") -> Dict[str, Any]:
        """
        Create a new user or get existing user data. Does not wipe data.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

        if user:
            cursor.execute("UPDATE users SET last_active = ? WHERE user_id = ?", (datetime.now(), user_id))
            if name is not None:
                cursor.execute("UPDATE users SET name = ? WHERE user_id = ?", (name, user_id))
            if age is not None:
                cursor.execute("UPDATE users SET age = ? WHERE user_id = ?", (age, user_id))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            _db_logger.info("User updated: user_id=%s", user_id)
        else:
            cursor.execute(
                "INSERT INTO users (user_id, parent_id, name, age) VALUES (?, ?, ?, ?)",
                (user_id, parent_id, name, age),
            )
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            _db_logger.info("User created: user_id=%s name=%s", user_id, name)

        conn.close()
        return dict(user)
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information by user ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def update_user_age(self, user_id: str, age: int) -> bool:
        """Update user's age."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET age = ? WHERE user_id = ?", (age, user_id))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def update_user_name(self, user_id: str, name: str) -> bool:
        """Replace a user's display name (used by teachers to rename
        anonymous ``Friend-XXXX`` accounts once the real child name is known)."""
        if not name or not name.strip():
            return False
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET name = ?, last_active = ? WHERE user_id = ?",
            (name.strip(), datetime.now(), user_id),
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        if affected:
            _db_logger.info("User renamed: user_id=%s -> %s", user_id, name.strip())
        return affected > 0

    def delete_user(self, user_id: str) -> bool:
        """
        Permanently delete a child (user) and all their data.
        For teachers/parents only. Removes: stars, sessions, classification_results,
        attention_results, visual_memory_results, then the user row.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM stars WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM classification_results WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM attention_results WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM visual_memory_results WHERE user_id = ?", (user_id,))
            for tbl in (
                "auditory_memory_results",
                "working_memory_results",
                "processing_speed_results",
                "final_assessment_results",
            ):
                try:
                    cursor.execute(f"DELETE FROM {tbl} WHERE user_id = ?", (user_id,))
                except sqlite3.OperationalError:
                    pass
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()
    
    # ==================== Session Recording ====================
    
    def record_session(self, user_id: str, module_name: str, accuracy: float = None,
                       time_spent_seconds: float = None, score: int = None,
                       max_score: int = None, additional_data: dict = None) -> int:
        """
        Record a general session/activity.
        
        Args:
            user_id: User identifier
            module_name: Name of the module (e.g., 'attention', 'visual_memory')
            accuracy: Accuracy score (0-1)
            time_spent_seconds: Time spent in seconds
            score: Points scored
            max_score: Maximum possible score
            additional_data: Any additional data as dictionary
            
        Returns:
            Session ID of the created record
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        additional_json = json.dumps(additional_data) if additional_data else None
        
        cursor.execute("""
            INSERT INTO sessions (user_id, module_name, accuracy, time_spent_seconds,
                                  score, max_score, additional_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, module_name, accuracy, time_spent_seconds, score, max_score, additional_json))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id
    
    # ==================== Classification Results ====================
    
    def record_classification(self, user_id: str, model_used: str, predicted_class: int,
                              predicted_label: str, confidence: float, probabilities: dict,
                              image_filename: str = None) -> int:
        """
        Record a classification result.
        
        Args:
            user_id: User identifier
            model_used: Name of the model used
            predicted_class: Predicted class index
            predicted_label: Human-readable label
            confidence: Confidence score
            probabilities: Dictionary of class probabilities
            image_filename: Original image filename
            
        Returns:
            Result ID of the created record
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        probs_json = json.dumps(probabilities)
        
        cursor.execute("""
            INSERT INTO classification_results 
            (user_id, model_used, predicted_class, predicted_label, confidence, 
             probabilities, image_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, model_used, predicted_class, predicted_label, confidence,
              probs_json, image_filename))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return result_id
    
    def get_classification_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent classification results for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM classification_results 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Parse JSON probabilities
        for result in results:
            if result.get('probabilities'):
                result['probabilities'] = json.loads(result['probabilities'])
        
        return results

    def delete_classification_result(self, result_id: int) -> bool:
        """Delete a single classification result by ID. For teachers/parents only."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM classification_results WHERE result_id = ?", (result_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    # ==================== Attention Module Results ====================
    
    def record_attention_result(self, user_id: str, target_letter: str, total_targets: int,
                                correct_clicks: int, incorrect_clicks: int, accuracy: float,
                                time_spent_seconds: float, focus_duration_target: int,
                                completed_duration: int, age_at_test: int) -> int:
        """
        Record an attention module assessment result.
        
        Args:
            user_id: User identifier
            target_letter: The letter user was supposed to find
            total_targets: Total number of target letters shown
            correct_clicks: Number of correct target clicks
            incorrect_clicks: Number of incorrect clicks
            accuracy: Accuracy score (0-1)
            time_spent_seconds: Total time spent
            focus_duration_target: Expected focus duration in minutes
            completed_duration: Actual completed duration in seconds
            age_at_test: User's age at time of test
            
        Returns:
            Result ID of the created record
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO attention_results 
            (user_id, target_letter, total_targets, correct_clicks, incorrect_clicks,
             accuracy, time_spent_seconds, focus_duration_target, completed_duration, age_at_test)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, target_letter, total_targets, correct_clicks, incorrect_clicks,
              accuracy, time_spent_seconds, focus_duration_target, completed_duration, age_at_test))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return result_id
    
    def get_attention_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent attention assessment results for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM attention_results 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def delete_attention_result(self, result_id: int) -> bool:
        """Delete a single attention result by ID. For teachers/parents only."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attention_results WHERE result_id = ?", (result_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    # ==================== Visual Memory Results ====================
    
    def record_visual_memory_result(self, user_id: str, grid_size: int,
                                    display_duration_seconds: float, total_questions: int,
                                    correct_answers: int, accuracy: float,
                                    time_spent_seconds: float, difficulty_level: str) -> int:
        """
        Record a visual memory module assessment result.
        
        Args:
            user_id: User identifier
            grid_size: Size of the memory grid (e.g., 3 for 3x3)
            display_duration_seconds: How long the grid was shown
            total_questions: Number of recall questions
            correct_answers: Number of correct answers
            accuracy: Accuracy score (0-1)
            time_spent_seconds: Total time spent
            difficulty_level: Difficulty level string
            
        Returns:
            Result ID of the created record
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO visual_memory_results 
            (user_id, grid_size, display_duration_seconds, total_questions,
             correct_answers, accuracy, time_spent_seconds, difficulty_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, grid_size, display_duration_seconds, total_questions,
              correct_answers, accuracy, time_spent_seconds, difficulty_level))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return result_id
    
    def get_visual_memory_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent visual memory assessment results for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM visual_memory_results 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def delete_visual_memory_result(self, result_id: int) -> bool:
        """Delete a single visual memory result by ID. For teachers/parents only."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM visual_memory_results WHERE result_id = ?", (result_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ==================== Auditory Memory Results ====================

    def record_auditory_memory_result(self, user_id: str, sequence_length: int,
                                      total_rounds: int, correct_rounds: int,
                                      accuracy: float, time_spent_seconds: float,
                                      difficulty_level: str, max_span_reached: int) -> int:
        """Record an auditory memory session."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO auditory_memory_results
            (user_id, sequence_length, total_rounds, correct_rounds, accuracy,
             time_spent_seconds, difficulty_level, max_span_reached)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, sequence_length, total_rounds, correct_rounds, accuracy,
              time_spent_seconds, difficulty_level, max_span_reached))
        rid = cursor.lastrowid
        conn.commit()
        conn.close()
        return rid

    def get_auditory_memory_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM auditory_memory_results
            WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def delete_auditory_memory_result(self, result_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auditory_memory_results WHERE result_id = ?", (result_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ==================== Working Memory (Digit Span) ====================

    def record_working_memory_result(self, user_id: str, mode: str, span_length: int,
                                     total_trials: int, correct_trials: int,
                                     accuracy: float, time_spent_seconds: float,
                                     max_span_reached: int) -> int:
        """Record a working memory (digit span) session."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO working_memory_results
            (user_id, mode, span_length, total_trials, correct_trials, accuracy,
             time_spent_seconds, max_span_reached)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, mode, span_length, total_trials, correct_trials, accuracy,
              time_spent_seconds, max_span_reached))
        rid = cursor.lastrowid
        conn.commit()
        conn.close()
        return rid

    def get_working_memory_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM working_memory_results
            WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def delete_working_memory_result(self, result_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM working_memory_results WHERE result_id = ?", (result_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ==================== Processing Speed ====================

    def record_processing_speed_result(self, user_id: str, task_type: str,
                                       total_trials: int, correct_trials: int,
                                       accuracy: float, avg_reaction_ms: float,
                                       time_spent_seconds: float,
                                       difficulty_level: str) -> int:
        """Record a processing speed session."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO processing_speed_results
            (user_id, task_type, total_trials, correct_trials, accuracy,
             avg_reaction_ms, time_spent_seconds, difficulty_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, task_type, total_trials, correct_trials, accuracy,
              avg_reaction_ms, time_spent_seconds, difficulty_level))
        rid = cursor.lastrowid
        conn.commit()
        conn.close()
        return rid

    def get_processing_speed_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM processing_speed_results
            WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def delete_processing_speed_result(self, result_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM processing_speed_results WHERE result_id = ?", (result_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ==================== Final Assessment ====================

    def record_final_assessment(self, user_id: str, overall_score: float,
                                attention_score: float, visual_memory_score: float,
                                auditory_memory_score: float, working_memory_score: float,
                                processing_speed_score: float, time_spent_seconds: float,
                                age_at_test: int, summary: str) -> int:
        """Record a final comprehensive assessment."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO final_assessment_results
            (user_id, overall_score, attention_score, visual_memory_score,
             auditory_memory_score, working_memory_score, processing_speed_score,
             time_spent_seconds, age_at_test, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, overall_score, attention_score, visual_memory_score,
              auditory_memory_score, working_memory_score, processing_speed_score,
              time_spent_seconds, age_at_test, summary))
        rid = cursor.lastrowid
        conn.commit()
        conn.close()
        return rid

    def get_final_assessment_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM final_assessment_results
            WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def delete_final_assessment_result(self, result_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM final_assessment_results WHERE result_id = ?", (result_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ==================== Progress Reports ====================
    
    def get_user_progress_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive progress summary for a user.
        
        Returns:
            Dictionary containing:
            - Total sessions per module
            - Average accuracy per module
            - Recent activity
            - Improvement trends
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        summary = {
            "user_id": user_id,
            "modules": {}
        }
        
        # Get attention module stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sessions,
                AVG(accuracy) as avg_accuracy,
                MAX(accuracy) as best_accuracy,
                AVG(time_spent_seconds) as avg_time,
                MAX(created_at) as last_session
            FROM attention_results
            WHERE user_id = ?
        """, (user_id,))
        attention_stats = dict(cursor.fetchone())
        if attention_stats['total_sessions'] > 0:
            summary['modules']['attention'] = attention_stats
        
        # Get visual memory stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sessions,
                AVG(accuracy) as avg_accuracy,
                MAX(accuracy) as best_accuracy,
                AVG(time_spent_seconds) as avg_time,
                MAX(created_at) as last_session
            FROM visual_memory_results
            WHERE user_id = ?
        """, (user_id,))
        memory_stats = dict(cursor.fetchone())
        if memory_stats['total_sessions'] > 0:
            summary['modules']['visual_memory'] = memory_stats

        for module_name, table in (
            ("auditory_memory", "auditory_memory_results"),
            ("working_memory", "working_memory_results"),
            ("processing_speed", "processing_speed_results"),
        ):
            try:
                cursor.execute(f"""
                    SELECT
                        COUNT(*) as total_sessions,
                        AVG(accuracy) as avg_accuracy,
                        MAX(accuracy) as best_accuracy,
                        AVG(time_spent_seconds) as avg_time,
                        MAX(created_at) as last_session
                    FROM {table}
                    WHERE user_id = ?
                """, (user_id,))
                row = cursor.fetchone()
                if row and row['total_sessions'] and row['total_sessions'] > 0:
                    summary['modules'][module_name] = dict(row)
            except sqlite3.OperationalError:
                pass

        # Get classification count
        cursor.execute("""
            SELECT COUNT(*) as total_classifications
            FROM classification_results
            WHERE user_id = ?
        """, (user_id,))
        summary['total_classifications'] = cursor.fetchone()['total_classifications']
        
        # Get general session stats
        cursor.execute("""
            SELECT 
                module_name,
                COUNT(*) as sessions,
                AVG(accuracy) as avg_accuracy
            FROM sessions
            WHERE user_id = ?
            GROUP BY module_name
        """, (user_id,))
        
        for row in cursor.fetchall():
            module_name = row['module_name']
            if module_name not in summary['modules']:
                summary['modules'][module_name] = {}
            summary['modules'][module_name].update({
                'sessions': row['sessions'],
                'avg_accuracy': row['avg_accuracy']
            })
        
        conn.close()
        return summary
    
    def get_all_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all sessions for a user across all modules."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Parse additional data JSON
        for result in results:
            if result.get('additional_data'):
                result['additional_data'] = json.loads(result['additional_data'])
        
        return results
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all data for a user (for backup or analysis).
        
        Returns:
            Dictionary containing all user data from all tables
        """
        return {
            "user_info": self.get_user(user_id),
            "classification_history": self.get_classification_history(user_id, limit=100),
            "attention_history": self.get_attention_history(user_id, limit=100),
            "visual_memory_history": self.get_visual_memory_history(user_id, limit=100),
            "auditory_memory_history": self.get_auditory_memory_history(user_id, limit=100),
            "working_memory_history": self.get_working_memory_history(user_id, limit=100),
            "processing_speed_history": self.get_processing_speed_history(user_id, limit=100),
            "final_assessment_history": self.get_final_assessment_history(user_id, limit=100),
            "all_sessions": self.get_all_sessions(user_id, limit=200),
            "progress_summary": self.get_user_progress_summary(user_id),
            "total_stars": self.get_total_stars(user_id)
        }
    
    # ==================== Stars / Gamification ====================
    
    def award_stars(self, user_id: str, module_name: str, stars: int, 
                    reason: str = None, session_id: int = None) -> int:
        """
        Award stars to a user for completing activities.
        
        Args:
            user_id: User identifier
            module_name: Name of the module (attention, visual_memory, etc.)
            stars: Number of stars to award
            reason: Reason for awarding stars
            session_id: Optional session ID to link stars to
            
        Returns:
            Star record ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO stars (user_id, module_name, stars_earned, reason, session_id)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, module_name, stars, reason, session_id))
        
        star_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return star_id
    
    def get_total_stars(self, user_id: str) -> int:
        """Get total stars earned by a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COALESCE(SUM(stars_earned), 0) as total_stars
            FROM stars
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['total_stars'] if result else 0
    
    def get_stars_by_module(self, user_id: str) -> Dict[str, int]:
        """Get stars earned per module."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT module_name, SUM(stars_earned) as stars
            FROM stars
            WHERE user_id = ?
            GROUP BY module_name
        """, (user_id,))
        
        results = {row['module_name']: row['stars'] for row in cursor.fetchall()}
        conn.close()
        
        return results
    
    def get_recent_stars(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent star awards."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM stars
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def calculate_stars_for_accuracy(self, accuracy: float) -> int:
        """
        Calculate stars to award based on accuracy.
        
        Star awarding logic:
        - 90%+ accuracy: 3 stars
        - 70-89% accuracy: 2 stars
        - 50-69% accuracy: 1 star
        - Below 50%: 1 star (participation)
        
        Args:
            accuracy: Accuracy score (0-1)
            
        Returns:
            Number of stars to award
        """
        if accuracy >= 0.9:
            return 3
        elif accuracy >= 0.7:
            return 2
        elif accuracy >= 0.5:
            return 1
        else:
            return 1  # Participation star
