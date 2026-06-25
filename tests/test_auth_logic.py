"""Tests for teacher/parent authentication logic."""

import pytest

from utils.auth import verify_teacher_credentials

DEFAULT_USER = "admin"
DEFAULT_PASS = "Teacher@123"


@pytest.mark.parametrize(
    "username,password,expected",
    [
        ("admin", "Teacher@123", True),
        (" admin ", "Teacher@123", True),
        ("Admin", "Teacher@123", False),
        ("admin", "wrong", False),
        ("", "Teacher@123", False),
        ("admin", "", False),
        ("", "", False),
    ],
)
def test_verify_teacher_credentials(username, password, expected):
    assert (
        verify_teacher_credentials(username, password, DEFAULT_USER, DEFAULT_PASS)
        is expected
    )
