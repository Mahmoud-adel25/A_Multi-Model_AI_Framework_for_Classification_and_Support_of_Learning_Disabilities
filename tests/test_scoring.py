"""Tests for support-module star scoring logic."""

import pytest


@pytest.mark.parametrize(
    "accuracy,expected",
    [
        (0.95, 3),
        (0.90, 3),
        (0.89, 2),
        (0.70, 2),
        (0.69, 1),
        (0.50, 1),
        (0.10, 1),
        (0.0, 1),
    ],
)
def test_calculate_stars_for_accuracy(db, accuracy, expected):
    assert db.calculate_stars_for_accuracy(accuracy) == expected
