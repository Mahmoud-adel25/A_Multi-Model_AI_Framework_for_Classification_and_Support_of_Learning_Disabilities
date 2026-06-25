"""Teacher/Parent credential verification (testable, no Streamlit dependency)."""

import hmac


def verify_teacher_credentials(
    username: str,
    password: str,
    expected_username: str,
    expected_password: str,
) -> bool:
    """Constant-time comparison of submitted vs expected admin credentials."""
    username_ok = hmac.compare_digest(username.strip(), expected_username)
    password_ok = hmac.compare_digest(password, expected_password)
    return username_ok and password_ok
