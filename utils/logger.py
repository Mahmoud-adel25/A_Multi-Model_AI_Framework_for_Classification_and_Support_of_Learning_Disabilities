"""
Logging utility for Learning Disability Detection System.

Console + optional UI logging for classification, DB operations,
child creation, and login. Used for demo stability and debugging.
"""

import logging
import sys
from datetime import datetime
from typing import Optional

# Configure root logger
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: str = "learning_support", level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger. Writes to console (stderr)."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    logger.addHandler(handler)
    return logger


def log_classification(logger: logging.Logger, model: str, shape: tuple, pred_class: int, label: str, conf: float):
    """Log classification inference."""
    logger.info(f"Classification | model={model} | input_shape={shape} | pred_class={pred_class} | label={label} | conf={conf:.4f}")


def log_db_op(logger: logging.Logger, op: str, table: str, detail: str = ""):
    """Log database operation."""
    logger.info(f"DB | op={op} | table={table} | {detail}")


def log_child_login(logger: logging.Logger, user_id: str, name: Optional[str], action: str):
    """Log child login/registration."""
    logger.info(f"Child | action={action} | user_id={user_id} | name={name}")


def log_error(logger: logging.Logger, context: str, error: Exception):
    """Log exception with context."""
    logger.exception(f"Error | context={context} | error={type(error).__name__}: {error}")
