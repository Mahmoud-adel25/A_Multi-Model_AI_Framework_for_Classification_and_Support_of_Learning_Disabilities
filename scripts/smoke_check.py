"""
Reproducible pre-flight system check.

Usage (from project root):
    python scripts/smoke_check.py

Exit 0 = all checks passed (or only non-critical weight warnings).
Exit 1 = critical failure.
"""

from __future__ import annotations

import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image

from database.db_handler import DatabaseHandler
from models.model_loader import ModelLoader
from utils.auth import verify_teacher_credentials
from utils.image_processing import ImageProcessor


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    print("=" * 60)
    print("SMOKE CHECK — Learning Disability Detection System")
    print("=" * 60)

    # 1. Database round-trip
    print("\n[1/5] Database insert/retrieve...")
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseHandler(db_path=str(Path(tmp) / "smoke.db"))
        uid = "smoke-user-001"
        db.create_or_get_user(uid, name="SmokeTest", age=8)
        if db.get_user(uid) is None:
            errors.append("DB create/get failed")
        else:
            db.record_attention_result(
                user_id=uid,
                target_letter="A",
                total_targets=5,
                correct_clicks=4,
                incorrect_clicks=1,
                accuracy=0.8,
                time_spent_seconds=20.0,
                focus_duration_target=3,
                completed_duration=18,
                age_at_test=8,
            )
            exported = db.export_user_data(uid)
            if not exported.get("attention_history"):
                errors.append("DB export missing attention history")
            else:
                print("  OK — user created, result stored, export non-empty")

    # 2. Star scoring
    print("\n[2/5] Support-module star scoring...")
    db_mem = DatabaseHandler(db_path=":memory:")
    if db_mem.calculate_stars_for_accuracy(0.95) != 3:
        errors.append("Star scoring: 95% should yield 3 stars")
    elif db_mem.calculate_stars_for_accuracy(0.40) != 1:
        errors.append("Star scoring: 40% should yield 1 star")
    else:
        print("  OK — star thresholds correct")

    # 3. Image validation
    print("\n[3/5] Image validation...")
    small = Image.new("RGB", (10, 10))
    ok, _ = ImageProcessor.validate_image(small)
    if ok:
        errors.append("Small image (10x10) should be rejected")
    else:
        valid = Image.new("RGB", (64, 64), color=(255, 255, 255))
        ok2, _ = ImageProcessor.validate_image(valid)
        if not ok2:
            errors.append("Valid 64x64 image should be accepted")
        else:
            buf = io.BytesIO(b"not-an-image")
            if ImageProcessor.load_image(buf) is not None:
                errors.append("Corrupt bytes should not load as image")
            else:
                print("  OK — rejects small/corrupt, accepts valid image")

    # 4. Authentication
    print("\n[4/5] Teacher authentication logic...")
    if not verify_teacher_credentials("admin", "Teacher@123", "admin", "Teacher@123"):
        errors.append("Valid credentials should authenticate")
    elif verify_teacher_credentials("admin", "wrong", "admin", "Teacher@123"):
        errors.append("Invalid password should not authenticate")
    else:
        print("  OK — credential verification works")

    # 5. Model checkpoints & inference
    print("\n[5/5] Model checkpoints and inference...")
    loader = ModelLoader()
    weights = loader.check_weights_available()
    print(f"  Weights on disk: {weights}")
    missing = [k for k, v in weights.items() if not v]
    if missing:
        warnings.append(
            f"Checkpoint files missing for: {', '.join(missing)} "
            "(place .pth files in models/ for full inference check)"
        )
    else:
        img = Image.new("L", (64, 64), color=255)
        for model_name in ("efficientnet", "mobilenet", "cnn"):
            result = loader.predict(img, model_name)
            if "error" in result:
                errors.append(f"predict({model_name}) error: {result['error']}")
            else:
                required = ("predicted_label", "confidence", "probabilities")
                for key in required:
                    if key not in result:
                        errors.append(f"predict({model_name}) missing key: {key}")
        if not any("predict(" in e for e in errors):
            print("  OK — all three models returned structured output")

    print("\n" + "=" * 60)
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    if errors:
        print("FAILED:")
        for e in errors:
            print(f"  - {e}")
        print("=" * 60)
        return 1

    print("SMOKE CHECK PASSED")
    if warnings:
        print("(with warnings — see above)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
