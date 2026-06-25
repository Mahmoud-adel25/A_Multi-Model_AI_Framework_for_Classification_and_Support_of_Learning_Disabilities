"""Tests for utils/image_processing.py — validation and loading."""

from PIL import Image

from utils.image_processing import ImageProcessor


def test_validate_accepts_normal_image(valid_image):
    ok, msg = ImageProcessor.validate_image(valid_image)
    assert ok is True
    assert msg == "Image is valid"


def test_validate_rejects_none():
    ok, msg = ImageProcessor.validate_image(None)
    assert ok is False
    assert "No image provided" in msg


def test_validate_rejects_small_image(small_image):
    ok, msg = ImageProcessor.validate_image(small_image)
    assert ok is False
    assert "too small" in msg.lower()


def test_validate_rejects_oversized_image():
    class OversizedImage:
        width = 5000
        height = 5000

    ok, msg = ImageProcessor.validate_image(OversizedImage())
    assert ok is False
    assert "too large" in msg.lower()


def test_load_image_from_bytes(valid_png_bytes):
    img = ImageProcessor.load_image(valid_png_bytes)
    assert img is not None
    assert img.size == (128, 128)


def test_load_image_corrupt_returns_none(corrupt_bytes):
    assert ImageProcessor.load_image(corrupt_bytes) is None


def test_load_image_from_path(valid_image, tmp_path):
    path = tmp_path / "letter.png"
    valid_image.save(path)
    img = ImageProcessor.load_image(str(path))
    assert img is not None
    assert img.size == (128, 128)
