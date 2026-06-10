"""
Model loading and inference for handwriting classification (Dyslexic vs Non-Dyslexic).

Aligned with Notebooks/Final code.ipynb:

- Labels: BINARY_CLASS_NAMES = ["Normal", "Dyslexia"] → 0=Normal, 1=Dyslexia.
  remap_synthetic_to_binary() maps folder "normal" → 0, others → 1.
  App displays 0=Non-Dyslexic, 1=Dyslexic (same meaning).

- CNN (3-class checkpoint):
  Notebook trains/evals CNN with 3 outputs; folder order = Corrected(0), Normal(1), Reversal(2).
  Preprocessing: Grayscale, Resize(28,28), ToTensor, Normalize(mean=0.5, std=0.5).
  We map: Non-Dyslexic = prob[1] (Normal), Dyslexic = prob[0]+prob[2] (Corrected+Reversal).

- EfficientNet-B0 / MobileNet V3 Large (2-class):
  Checkpoints trained with 0=Dyslexia, 1=Normal. App displays 0=Non-Dyslexic, 1=Dyslexic.
  Both MOBILENET_SWAP_CLASS_INDEX and EFFICIENTNET_SWAP_CLASS_INDEX are True to flip predictions.
"""

import os
from typing import Dict, Any, Optional, Tuple

import torch
import numpy as np
from PIL import Image, ImageOps

from utils.image_processing import ImageProcessor
from .cnn_model import CNNClassifier
from .mobilenet_model import MobileNetClassifier
from .efficientnet_model import EfficientNetClassifier


NUM_CLASSES = 2
CLASS_LABELS = {0: "Non-Dyslexic", 1: "Dyslexic"}

CNN_NUM_CLASSES = 3
CNN_DYSLEXIC_THRESHOLD = 0.5
# If CNN predictions are inverted vs expected, set to True (Non-Dyslexic = Corrected+Reversal, Dyslexic = Normal)
CNN_INVERT_BINARY = False

# Checkpoints use 0=Dyslexia, 1=Normal; app displays 0=Non-Dyslexic, 1=Dyslexic → swap both
MOBILENET_SWAP_CLASS_INDEX = True  # mobilenet_v3_large_classifier.pth: 0=Dyslexia, 1=Normal → swap for display
EFFICIENTNET_SWAP_CLASS_INDEX = True  # efficientnet_b0_classifier (1).pth: 0=Dyslexia, 1=Normal → swap for display

_MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
CNN_CHECKPOINT = os.path.join(_MODEL_DIR, "cnn_classifier (2).pth")
MOBILENET_CHECKPOINT = os.path.join(_MODEL_DIR, "mobilenet_v3_large_classifier.pth")
EFFICIENTNET_CHECKPOINT = os.path.join(_MODEL_DIR, "efficientnet_b0_classifier (1).pth")


def _get_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _transformation_note() -> str:
    return (
        "Classification can differ on reversed or transformed versions of the same handwriting. "
        "Models use visual features (orientation, stroke direction, layout) that can vary with transformation."
    )


def _prepare_cnn_image(pil_image: Image.Image) -> torch.Tensor:
    image = ImageOps.exif_transpose(pil_image)
    if image.mode != "L":
        image = image.convert("L")
    resized = image.resize((28, 28), Image.Resampling.LANCZOS)
    arr = np.array(resized, dtype=np.float32) / 255.0
    arr = (arr - 0.5) / 0.5
    return torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)


def _prepare_effnet_image(pil_image: Image.Image) -> torch.Tensor:
    image = ImageOps.exif_transpose(pil_image)
    if image.mode != "L":
        image = image.convert("L")
    w, h = image.size
    side = max(w, h)
    padded = Image.new("L", (side, side), 255)
    padded.paste(image, ((side - w) // 2, (side - h) // 2))
    resized = padded.resize((224, 224), Image.Resampling.LANCZOS)
    arr = np.array(resized, dtype=np.float32) / 255.0
    arr = np.stack([arr, arr, arr], axis=-1)
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    arr = (arr - mean) / std
    return torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)


def _cnn_three_class_to_binary(probs_3: np.ndarray) -> Tuple[int, float, Dict[str, float]]:
    """Non-Dyslexic = Normal (1), Dyslexic = Corrected (0) + Reversal (2). Invert if CNN_INVERT_BINARY."""
    if CNN_INVERT_BINARY:
        p_non = float(probs_3[0]) + float(probs_3[2])
        p_dys = float(probs_3[1])
    else:
        p_non = float(probs_3[1])
        p_dys = float(probs_3[0]) + float(probs_3[2])
    total = p_non + p_dys
    if total > 0:
        p_non, p_dys = p_non / total, p_dys / total
    else:
        p_non, p_dys = 0.5, 0.5
    binary_probs = {"Non-Dyslexic": p_non, "Dyslexic": p_dys}
    pred_class = 1 if p_dys >= CNN_DYSLEXIC_THRESHOLD else 0
    conf = max(p_non, p_dys)
    return pred_class, conf, binary_probs


class ModelLoader:
    def __init__(self):
        self._device = _get_device()
        self._models: Dict[str, Any] = {}
        self._loaded: Dict[str, bool] = {}

    def get_device(self) -> str:
        return "cuda" if self._device.type == "cuda" else "cpu"

    def check_weights_available(self) -> Dict[str, bool]:
        return {
            "cnn": os.path.isfile(CNN_CHECKPOINT),
            "mobilenet": os.path.isfile(MOBILENET_CHECKPOINT),
            "efficientnet": os.path.isfile(EFFICIENTNET_CHECKPOINT),
        }

    def is_model_loaded(self, model_name: str) -> bool:
        return self._loaded.get(model_name, False)

    def load_model(self, model_name: str) -> None:
        if model_name == "cnn":
            model = CNNClassifier(num_classes=CNN_NUM_CLASSES)
            ckpt = torch.load(CNN_CHECKPOINT, map_location=self._device)
            model.load_state_dict(ckpt.get("model_state_dict", ckpt), strict=True)
            model.eval()
            self._models["cnn"] = model.to(self._device)
            self._loaded["cnn"] = True
        elif model_name == "mobilenet":
            model = MobileNetClassifier(num_classes=NUM_CLASSES, pretrained_backbone=False)
            ckpt = torch.load(MOBILENET_CHECKPOINT, map_location=self._device)
            model.load_state_dict(ckpt.get("model_state_dict", ckpt), strict=True)
            model.eval()
            self._models["mobilenet"] = model.to(self._device)
            self._loaded["mobilenet"] = True
        elif model_name == "efficientnet":
            model = EfficientNetClassifier(num_classes=NUM_CLASSES, pretrained_backbone=False)
            ckpt = torch.load(EFFICIENTNET_CHECKPOINT, map_location=self._device)
            model.load_state_dict(ckpt.get("model_state_dict", ckpt), strict=True)
            model.eval()
            self._models["efficientnet"] = model.to(self._device)
            self._loaded["efficientnet"] = True
        else:
            raise ValueError(f"Unknown model: {model_name}")

    def predict(self, image, model_name: str) -> Dict[str, Any]:
        if not self.is_model_loaded(model_name):
            self.load_model(model_name)

        pil = image
        if not isinstance(pil, Image.Image):
            pil = ImageProcessor.load_image(pil)
        if pil is None:
            return {"error": "Could not load image"}

        model = self._models[model_name]
        model_note: Optional[str] = None

        if model_name == "cnn":
            tensor = _prepare_cnn_image(pil).to(self._device)
            with torch.no_grad():
                logits = model(tensor)
            logits = logits.cpu()
            probs_3 = torch.softmax(logits, dim=1).numpy()[0]
            pred_class, conf, probs = _cnn_three_class_to_binary(probs_3)
            debug = {
                "input_shape": tuple(tensor.shape),
                "output_shape": tuple(logits.shape),
                "predicted_class_index": int(pred_class),
                "device": str(self._device),
            }
            model_note = _transformation_note()
        else:
            tensor = _prepare_effnet_image(pil).to(self._device)
            with torch.no_grad():
                logits = model(tensor)
            logits = logits.cpu()
            probs = torch.softmax(logits, dim=1).numpy()[0]
            if model_name == "mobilenet" and MOBILENET_SWAP_CLASS_INDEX:
                probs = np.array([probs[1], probs[0]])
            if model_name == "efficientnet" and EFFICIENTNET_SWAP_CLASS_INDEX:
                probs = np.array([probs[1], probs[0]])
            pred_idx = int(np.argmax(probs))
            conf = float(probs[pred_idx])
            pred_class = pred_idx
            probs = {CLASS_LABELS[i]: float(probs[i]) for i in range(NUM_CLASSES)}
            debug = {
                "input_shape": tuple(tensor.shape),
                "output_shape": tuple(logits.shape),
                "predicted_class_index": pred_idx,
                "device": str(self._device),
            }
            model_note = _transformation_note()

        label = CLASS_LABELS[pred_class]
        out = {
            "model_used": model_name,
            "predicted_class": pred_class,
            "predicted_label": label,
            "confidence": conf,
            "probabilities": probs,
            "debug_info": debug,
        }
        if model_note:
            out["model_note"] = model_note
        return out
