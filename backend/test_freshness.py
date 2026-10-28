"""
Epic 3 — Freshness Detector: comprehensive pytest test suite.

Tests cover:
  - Empty plate / low-information → Inconclusive
  - Fresh food → Fresh
  - Brown-rot food → Spoiled
  - Grey/faded food → Spoiled
  - Teal mould → Spoiled
  - Mixed spoilage → Moderate
  - Fresh food on white plate → not Spoiled (edge case)
  - Error handling (corrupt bytes, too-small images)
"""

import io
import pytest
import numpy as np
from PIL import Image

from routers.freshness_detector import (
    _validate_and_decode,
    _preprocess,
    _extract_features,
    _compute_freshness_score,
    _classify,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_image(rgb, size=(200, 200)):
    """Create a uniform-colour JPEG from an RGB tuple."""
    arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    arr[:, :] = rgb
    return _to_jpeg(Image.fromarray(arr, "RGB"))


def _to_jpeg(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def _analyse(raw_bytes: bytes, category: str = "generic"):
    """Run the full pipeline and return (features, score, label, safety, signs)."""
    img = _validate_and_decode(raw_bytes)
    proc, _meta = _preprocess(img)
    feats = _extract_features(proc)
    score, signs = _compute_freshness_score(feats, category)
    label, safety = _classify(score)
    return feats, score, label, safety, signs


# ===========================================================================
# 1.  Empty plate / low-information images → Inconclusive
# ===========================================================================

class TestEmptyPlate:
    """Images that are featureless should be Inconclusive, not Spoiled."""

    def test_white_plate(self):
        raw = _make_image([245, 245, 240])
        feats, score, label, safety, signs = _analyse(raw, "generic")
        assert feats["low_information"] is True, "white plate should be low_information"
        assert score == -1
        assert label == "Inconclusive"
        assert safety == "unable_to_assess"

    def test_light_grey_background(self):
        raw = _make_image([200, 200, 200])
        _, score, label, _, _ = _analyse(raw, "generic")
        assert label == "Inconclusive"

    def test_black_surface(self):
        """A pure-black surface — dark_fraction is high, so low_information
        should be False.  It should NOT be labelled as Fresh."""
        raw = _make_image([5, 5, 5])
        feats, score, label, _, _ = _analyse(raw, "generic")
        assert label != "Fresh"


# ===========================================================================
# 2.  Fresh food → Fresh
# ===========================================================================

class TestFreshFood:
    """Vivid, saturated food images should classify as Fresh."""

    def test_fresh_green_apple(self):
        raw = _make_image([60, 160, 60])
        _, score, label, safety, signs = _analyse(raw, "fruit")
        assert label == "Fresh"
        assert score >= 90
        assert safety == "safe_to_consume"
        assert len(signs) == 0

    def test_fresh_red_tomato(self):
        raw = _make_image([200, 50, 40])
        _, score, label, _, _ = _analyse(raw, "vegetable")
        assert label == "Fresh"
        assert score >= 90

    def test_fresh_orange_carrot(self):
        raw = _make_image([220, 120, 20])
        _, score, label, _, _ = _analyse(raw, "vegetable")
        assert label == "Fresh"
        assert score >= 90


# ===========================================================================
# 3.  Brown-rot food → Spoiled
# ===========================================================================

class TestBrownRot:
    """Brown-rot images should be classified as Spoiled, not Moderate."""

    def test_brown_rot_fruit(self):
        raw = _make_image([90, 50, 20])
        feats, score, label, safety, signs = _analyse(raw, "fruit")
        assert feats["brown_rot_fraction"] > 0.5, \
            f"brown_rot_fraction should be high, got {feats['brown_rot_fraction']}"
        assert label == "Spoiled", f"Expected Spoiled, got {label} (score={score})"
        assert safety == "do_not_consume"
        assert score < 45

    def test_brown_rot_vegetable(self):
        raw = _make_image([90, 50, 20])
        _, score, label, _, _ = _analyse(raw, "vegetable")
        assert label == "Spoiled"
        assert score < 45


# ===========================================================================
# 4.  Grey/faded and teal mould → Spoiled
# ===========================================================================

class TestSpoiledCues:

    def test_grey_faded_food(self):
        raw = _make_image([130, 130, 125])
        feats, score, label, _, _ = _analyse(raw, "cooked")
        assert feats["grey_fraction"] > 0.5
        assert label == "Spoiled"

    def test_teal_mould(self):
        raw = _make_image([30, 180, 150])
        feats, score, label, _, signs = _analyse(raw, "vegetable")
        assert feats["mould_teal_fraction"] > 0.5
        assert label == "Spoiled"
        assert score == 0


# ===========================================================================
# 5.  Mixed spoilage → Moderate
# ===========================================================================

class TestMixedSpoilage:

    def test_brown_and_dark_grey_mix(self):
        """Upper portion brown, lower portion dark grey — Moderate."""
        arr = np.zeros((200, 200, 3), dtype=np.uint8)
        arr[:130, :] = [85, 48, 18]
        arr[130:, :] = [38, 38, 38]
        raw = _to_jpeg(Image.fromarray(arr, "RGB"))
        _, score, label, _, _ = _analyse(raw, "vegetable")
        # Should be Moderate (45-71) or Spoiled — not Fresh
        assert label in ("Moderate", "Spoiled")
        assert score < 72


# ===========================================================================
# 6.  Fresh food on white plate (edge case)
# ===========================================================================

class TestFreshOnWhitePlate:
    """A small food portion on a large white plate should not be 'Spoiled'.
    The white plate area triggers mould_white_mask, but the overall image
    has enough vivid colour content to avoid low_information, so it won't
    be Inconclusive.  It should be at least Moderate, not Spoiled."""

    def test_red_food_on_white_plate(self):
        arr = np.zeros((200, 200, 3), dtype=np.uint8)
        arr[:, :] = [245, 245, 240]       # white plate
        arr[50:150, 50:150] = [200, 50, 40]  # red food in center
        raw = _to_jpeg(Image.fromarray(arr, "RGB"))
        feats, score, label, _, _ = _analyse(raw, "vegetable")
        assert feats["low_information"] is False
        assert label != "Spoiled", \
            f"Fresh food on white plate should not be Spoiled (score={score})"

    def test_green_food_on_white_plate(self):
        arr = np.zeros((200, 200, 3), dtype=np.uint8)
        arr[:, :] = [245, 245, 240]
        arr[40:160, 40:160] = [60, 160, 60]
        raw = _to_jpeg(Image.fromarray(arr, "RGB"))
        _, score, label, _, _ = _analyse(raw, "fruit")
        assert label != "Spoiled"


# ===========================================================================
# 7.  Error handling
# ===========================================================================

class TestErrorHandling:

    def test_corrupt_bytes_raises(self):
        with pytest.raises(ValueError, match="Cannot decode image"):
            _validate_and_decode(b"notanimage")

    def test_too_small_image_raises(self):
        arr = np.zeros((20, 20, 3), dtype=np.uint8)
        img = Image.fromarray(arr, "RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        with pytest.raises(ValueError, match="Image too small"):
            _validate_and_decode(buf.getvalue())


# ===========================================================================
# 8.  Realistic edge cases (Epic 3 investigation)
# ===========================================================================

class TestRealisticEdgeCases:

    def test_realistic_shaded_white_plate_is_inconclusive(self):
        """Clean white plate with subtle radial shading must not be marked Spoiled."""
        h, w = 200, 200
        y, x = np.ogrid[:h, :w]
        plate = 240 - 20 * ((x - 100)**2 + (y - 100)**2) / (100**2 + 100**2)
        plate = np.stack([plate, plate, plate - 5], axis=-1).astype(np.uint8)
        raw = _to_jpeg(Image.fromarray(plate, "RGB"))
        feats, score, label, safety, _ = _analyse(raw, "generic")
        assert feats["low_information"] is True
        assert score == -1
        assert label == "Inconclusive"
        assert safety == "unable_to_assess"

    def test_fruit_with_partial_brown_rot_is_spoiled(self):
        """A fruit with 25% brown rot lesion must be classified as Spoiled, not Moderate."""
        fruit = np.zeros((200, 200, 3), dtype=np.uint8)
        fruit[:, :] = [200, 40, 40]   # vivid red surface
        fruit[:50, :] = [90, 50, 20]   # 25% deep brown rot lesion
        raw = _to_jpeg(Image.fromarray(fruit, "RGB"))
        feats, score, label, safety, signs = _analyse(raw, "fruit")
        assert feats["brown_rot_fraction"] >= 0.20
        assert label == "Spoiled"
        assert score < 45
        assert safety == "do_not_consume"
        assert any("rot" in s.lower() or "decay" in s.lower() for s in signs)


# ===========================================================================
# 9. Phase 5: Freshness Pipeline, Status, Model Manager & Honest Disclosures
# ===========================================================================

class TestPhase5FreshnessPipeline:

    def test_freshness_status_endpoint(self):
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)

        resp = client.get("/api/v1/food/freshness/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "model_loaded" in data
        assert "model_id" in data
        assert "analysis_mode" in data
        assert "limitations_notice" in data
        assert "Salmonella" in data["limitations_notice"]

    def test_freshness_endpoint_returns_honest_disclosure_and_visual_evidence(self):
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)

        # Fresh tomato-like image
        arr = np.zeros((100, 100, 3), dtype=np.uint8)
        arr[:, :] = [200, 50, 40]
        raw = _to_jpeg(Image.fromarray(arr, "RGB"))

        resp = client.post(
            "/api/v1/food/freshness",
            files={"file": ("tomato.jpg", raw, "image/jpeg")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "model_id" in data
        assert "analysis_mode" in data
        assert data["analysis_mode"] in ("heuristic_visual_cues", "deep_learning_model")
        assert "visual_evidence" in data
        assert "browning_detected" in data["visual_evidence"]
        assert "mold_detected" in data["visual_evidence"]
        assert "limitations" in data
        assert any("microbial" in lim.lower() for lim in data["limitations"])
        assert "pipeline_disclosure" in data

    def test_freshness_model_manager_load_and_unload(self, tmp_path):
        import json
        import torch
        import torch.nn as nn
        from torchvision import models
        from routers.freshness_detector import freshness_manager

        # Create dummy MobileNetV3 freshness checkpoint
        model = models.mobilenet_v3_small(weights=None)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, 2)

        ckpt_path = tmp_path / "freshness_test.pt"
        torch.save({
            "model_state_dict": model.state_dict(),
            "backbone": "mobilenet_v3_small",
            "num_classes": 2,
        }, ckpt_path)

        mapping_path = tmp_path / "class_mapping.json"
        mapping_path.write_text(json.dumps({
            "id2label": {"0": "fresh", "1": "spoiled"},
            "label2id": {"fresh": 0, "spoiled": 1},
        }))

        try:
            loaded = freshness_manager.load_model(ckpt_path, mapping_path, device="cpu")
            assert loaded is True
            assert freshness_manager.is_model_loaded is True
            assert freshness_manager.analysis_mode == "deep_learning_model"
            assert "mobilenet_v3" in freshness_manager.model_id

            # Predict on a test image
            test_img = Image.new("RGB", (100, 100), color=(50, 150, 50))
            pred = freshness_manager.predict(test_img)
            assert pred is not None
            assert pred["predicted_class"] in ("fresh", "spoiled")
            assert 0.0 <= pred["confidence"] <= 1.0
            assert "class_probabilities" in pred

        finally:
            freshness_manager.unload_model()
            assert freshness_manager.is_model_loaded is False
            assert freshness_manager.analysis_mode == "heuristic_visual_cues"

    def test_freshness_model_manager_missing_files_raises(self):
        from routers.freshness_detector import freshness_manager
        with pytest.raises(FileNotFoundError, match="Checkpoint not found"):
            freshness_manager.load_model("nonexistent_path_123.pt", "mapping.json")

