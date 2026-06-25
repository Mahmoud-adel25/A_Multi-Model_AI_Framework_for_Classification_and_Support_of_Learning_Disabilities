"""Tests for models/model_loader.py — checkpoints and prediction output."""

import pytest
from PIL import Image

from models.model_loader import (
    CLASS_LABELS,
    ModelLoader,
    _cnn_three_class_to_binary,
)


def test_check_weights_available_keys():
    loader = ModelLoader()
    status = loader.check_weights_available()
    assert set(status.keys()) == {"cnn", "mobilenet", "efficientnet"}
    assert all(isinstance(v, bool) for v in status.values())


def test_check_weights_all_missing_when_files_absent(monkeypatch):
    monkeypatch.setattr("models.model_loader.os.path.isfile", lambda _p: False)
    loader = ModelLoader()
    status = loader.check_weights_available()
    assert status == {"cnn": False, "mobilenet": False, "efficientnet": False}


def test_load_model_raises_for_unknown():
    loader = ModelLoader()
    with pytest.raises(ValueError, match="Unknown model"):
        loader.load_model("not-a-model")


def test_load_model_missing_checkpoint_raises(monkeypatch):
    monkeypatch.setattr(
        "models.model_loader.EFFICIENTNET_CHECKPOINT",
        "/nonexistent/efficientnet_weights.pth",
    )
    loader = ModelLoader()
    with pytest.raises((FileNotFoundError, OSError)):
        loader.load_model("efficientnet")


def test_cnn_three_class_to_binary_mapping():
    # Normal-heavy: class 1 dominates → Non-Dyslexic
    probs = [0.1, 0.8, 0.1]
    pred_class, conf, binary = _cnn_three_class_to_binary(probs)
    assert pred_class == 0
    assert binary["Non-Dyslexic"] > binary["Dyslexic"]
    assert 0 <= conf <= 1


def test_cnn_three_class_dyslexic_when_corrected_and_reversal_high():
    probs = [0.45, 0.05, 0.50]
    pred_class, _, binary = _cnn_three_class_to_binary(probs)
    assert binary["Dyslexic"] >= 0.5
    assert pred_class == 1


def test_predict_output_schema_when_weights_available(valid_image):
    loader = ModelLoader()
    if not loader.check_weights_available()["efficientnet"]:
        pytest.skip("EfficientNet checkpoint not on disk")

    result = loader.predict(valid_image, "efficientnet")
    assert "error" not in result
    for key in (
        "model_used",
        "predicted_class",
        "predicted_label",
        "confidence",
        "probabilities",
        "debug_info",
    ):
        assert key in result

    assert result["predicted_label"] in CLASS_LABELS.values()
    assert 0 <= result["confidence"] <= 1
    assert set(result["probabilities"].keys()) == set(CLASS_LABELS.values())


@pytest.mark.parametrize("model_name", ["cnn", "mobilenet", "efficientnet"])
def test_predict_each_model_when_weights_available(valid_image, model_name):
    loader = ModelLoader()
    if not loader.check_weights_available()[model_name]:
        pytest.skip(f"{model_name} checkpoint not on disk")

    result = loader.predict(valid_image, model_name)
    assert "error" not in result
    assert result["model_used"] == model_name
    assert result["predicted_label"] in ("Non-Dyslexic", "Dyslexic")


def test_predict_none_image_returns_error():
    loader = ModelLoader()
    result = loader.predict(None, "efficientnet")
    assert result.get("error") == "Could not load image"
