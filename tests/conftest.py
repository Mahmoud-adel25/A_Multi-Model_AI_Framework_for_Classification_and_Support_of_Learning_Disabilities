"""Shared pytest fixtures."""

import io
import sys
from pathlib import Path

import pytest
from PIL import Image

# Project root on sys.path for imports
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def db(tmp_path):
    from database.db_handler import DatabaseHandler

    return DatabaseHandler(db_path=str(tmp_path / "test.db"))


@pytest.fixture
def valid_image():
    return Image.new("RGB", (128, 128), color=(255, 255, 255))


@pytest.fixture
def small_image():
    return Image.new("RGB", (16, 16), color=(255, 255, 255))


@pytest.fixture
def valid_png_bytes(valid_image):
    buf = io.BytesIO()
    valid_image.save(buf, format="PNG")
    buf.seek(0)
    return buf


@pytest.fixture
def corrupt_bytes():
    return io.BytesIO(b"this is not a valid image file")
