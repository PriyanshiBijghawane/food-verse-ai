"""
Epic 4.1 & Phase 6 — Hygiene Monitor Tests
==========================================
Tests cover:
- Valid kitchen image audit
- Corrupt image error handling
- Undersized image rejection
- Video processing and frame extraction
- Unsupported media rejection
- Cleanliness and compliance scoring logic
- Report retrieval in JSON and markdown formats
- Status endpoint reporting operational state and model manager metadata
- Honest heuristic disclosures and absence of fabricated confidence
- Video sampling limits, timestamps, and continuous monitoring disclaimers
- Video deduplication: repeated frame findings aggregated without multi-penalizing
- Video duration limit enforcement (> 120s rejected)
- Temporary file cleanup verification on success and decoding failure
- Modular detector loading/unloading with real model confidences
- Unsupported detection classes rejection and lack of fabricated detections
"""

import io
import os
import tempfile
from typing import Any

import cv2
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from main import app
from routers.hygiene_monitor import (
    HygieneDetectorInterface,
    hygiene_model_manager,
    _detector_hygiene_audit,
)

client = TestClient(app)


def _make_jpeg_bytes(rgb=(200, 200, 200), size=(200, 200)) -> bytes:
    arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    arr[:, :] = rgb
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_sample_video_bytes(duration_frames=15, fps=10.0, size=(160, 120), rgb=None) -> bytes:
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
    os.close(tmp_fd)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(tmp_path, fourcc, float(fps), size)
    for i in range(duration_frames):
        frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        if rgb is not None:
            # OpenCV expects BGR
            frame[:, :] = [rgb[2], rgb[1], rgb[0]]
        else:
            frame[:, :] = [(i * 15) % 255, 180, 180]
        out.write(frame)
    out.release()

    with open(tmp_path, "rb") as f:
        data = f.read()
    try:
        os.remove(tmp_path)
    except Exception:
        pass
    return data


# ===========================================================================
# 1. Image Audit Tests
# ===========================================================================

class TestHygieneImageAudit:

    def test_clean_kitchen_image_audit(self):
        img_bytes = _make_jpeg_bytes(rgb=(190, 195, 200), size=(300, 300))
        resp = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("kitchen.jpg", img_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "audit_id" in data
        assert data["media_type"] == "image"
        assert data["frames_analyzed"] == 1
        assert 0 <= data["compliance_score"] <= 100
        assert 0 <= data["cleanliness_score"] <= 100
        assert "ai_summary" in data
        assert "observations" in data

    def test_corrupt_image_rejected(self):
        resp = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("corrupt.jpg", b"not_an_image_data", "image/jpeg")},
        )
        assert resp.status_code == 400
        assert "Invalid image file" in resp.json()["detail"]

    def test_undersized_image_rejected(self):
        tiny_bytes = _make_jpeg_bytes(size=(32, 32))
        resp = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("tiny.jpg", tiny_bytes, "image/jpeg")},
        )
        assert resp.status_code == 400
        assert "too small" in resp.json()["detail"].lower()

    def test_unsupported_media_rejected(self):
        resp = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("document.pdf", b"%PDF-1.4...", "application/pdf")},
        )
        assert resp.status_code == 400
        assert "Unsupported media type" in resp.json()["detail"]


# ===========================================================================
# 2. Video Audit Tests
# ===========================================================================

class TestHygieneVideoAudit:

    def test_valid_video_footage_audit(self):
        vid_bytes = _make_sample_video_bytes(duration_frames=20)
        resp = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("cctv_clip.mp4", vid_bytes, "video/mp4")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["media_type"] == "video"
        assert data["frames_analyzed"] >= 1
        assert "violations" in data

    def test_corrupt_video_rejected(self):
        resp = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("broken.mp4", b"corrupt_mp4_bytes", "video/mp4")},
        )
        assert resp.status_code == 400


# ===========================================================================
# 3. Report Retrieval Tests
# ===========================================================================

class TestHygieneReportRetrieval:

    def test_report_json_and_markdown_download(self):
        img_bytes = _make_jpeg_bytes(rgb=(180, 180, 180), size=(200, 200))
        post_resp = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("counter.jpg", img_bytes, "image/jpeg")},
        )
        assert post_resp.status_code == 200
        audit_id = post_resp.json()["audit_id"]

        # 1. Fetch JSON report
        get_json = client.get(f"/api/v1/hygiene/report/{audit_id}?format=json")
        assert get_json.status_code == 200
        assert get_json.json()["audit_id"] == audit_id

        # 2. Fetch Markdown report
        get_md = client.get(f"/api/v1/hygiene/report/{audit_id}?format=markdown")
        assert get_md.status_code == 200
        assert "Commercial Kitchen Hygiene Audit Report" in get_md.text
        assert audit_id in get_md.text

    def test_nonexistent_report_404(self):
        resp = client.get("/api/v1/hygiene/report/NONEXISTENT123")
        assert resp.status_code == 404


# ===========================================================================
# 4. Status Endpoint Tests
# ===========================================================================

class TestHygieneStatus:

    def test_status_endpoint_returns_operational_metadata(self):
        resp = client.get("/api/v1/hygiene/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"
        assert data["analysis_mode"] == "heuristic_visual_cues"
        assert data["model_loaded"] is False
        assert "local_cv_hygiene_heuristics_v1" in data["model_id"]
        assert "surface_spill_candidate" in data["supported_classes"]
        assert "workstation_clutter_candidate" in data["supported_classes"]
        assert data["max_video_duration_sec"] == 120.0
        assert data["max_sampled_frames"] == 8


# ===========================================================================
# 5. Honest Disclosures & Heuristic Precision Tests
# ===========================================================================

class TestHygieneHonestDisclosures:

    def test_clean_image_audit_disclosures(self):
        img_bytes = _make_jpeg_bytes(rgb=(190, 195, 200), size=(200, 200))
        resp = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("clean.jpg", img_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["analysis_mode"] == "heuristic_visual_cues"
        assert data["model_loaded"] is False
        assert "local_cv_hygiene_heuristics_v1" in data["model_id"]
        assert "monitoring_scope" in data
        assert data["monitoring_scope"] == "single_frame_capture"

        # Limitations must explicitly state what cannot be detected
        assert isinstance(data["limitations"], list)
        assert len(data["limitations"]) >= 4
        limitations_text = " ".join(data["limitations"]).lower()
        assert "pathogen" in limitations_text or "bacteria" in limitations_text
        assert "continuous" in limitations_text
        assert "temperatures" in limitations_text or "chemical" in limitations_text

        # Uncertainty guidance must be present
        assert isinstance(data["uncertainty_and_human_review"], list)
        assert len(data["uncertainty_and_human_review"]) >= 2

    def test_spill_detection_heuristics_no_fake_confidence(self):
        # Dark, high saturation RGB patch triggers spill heuristics (V < 0.25, S > 0.20)
        spill_bytes = _make_jpeg_bytes(rgb=(50, 10, 10), size=(200, 200))
        resp = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("spill_surface.jpg", spill_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["violations"]) >= 1

        spill_violations = [v for v in data["violations"] if "Spill" in v["violation_type"]]
        assert len(spill_violations) == 1
        v = spill_violations[0]
        # Crucial check: in heuristic mode, confidence must be None, never a fabricated float
        assert v["confidence"] is None
        assert v["requires_human_review"] is True
        assert "human_review_reason" in v
        assert len(v["observed_timestamps_sec"]) == 1


# ===========================================================================
# 6. Advanced Video Tests (Limits, Sampling, Deduplication, Safe Cleanup)
# ===========================================================================

class TestHygieneVideoAdvanced:

    def test_video_sampling_limits_and_sampling_metadata(self):
        # Create video with 25 frames
        vid_bytes = _make_sample_video_bytes(duration_frames=25, fps=10.0)
        resp = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("patrol_clip.mp4", vid_bytes, "video/mp4")},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Must not sample unbounded frames
        assert data["frames_analyzed"] <= 8
        assert data["monitoring_scope"] == "sampled_discrete_frames (non-continuous monitoring)"

        meta = data["sampling_metadata"]
        assert meta["is_continuous_monitoring"] is False
        assert meta["video_duration_sec"] == 2.5
        assert meta["sampled_frame_count"] == data["frames_analyzed"]
        assert "non-continuous" in meta["sampling_disclosure"].lower() or "not represent" in meta["sampling_disclosure"].lower()

    def test_video_repeated_spill_frame_deduplication(self):
        # Video where all frames have dark saturated spill (RGB: 50, 10, 10)
        vid_bytes = _make_sample_video_bytes(duration_frames=16, fps=8.0, rgb=(50, 10, 10))
        resp = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("spill_footage.mp4", vid_bytes, "video/mp4")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["frames_analyzed"] >= 2

        spill_violations = [v for v in data["violations"] if "Spill" in v["violation_type"]]
        # Must deduplicate repeated frames into ONE single violation entry
        assert len(spill_violations) == 1
        v = spill_violations[0]
        assert v["occurrences"] >= 2
        assert len(v["observed_timestamps_sec"]) >= 2
        # Compliance score penalized once for the violation, not multi-penalized per frame
        assert data["compliance_score"] >= 70

    def test_video_duration_exceeded_rejected(self):
        # 130 frames at 1.0 fps = 130.0s > 120.0s limit
        long_vid_bytes = _make_sample_video_bytes(duration_frames=130, fps=1.0, size=(80, 60))
        resp = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("too_long.mp4", long_vid_bytes, "video/mp4")},
        )
        assert resp.status_code == 400
        assert "exceeds maximum allowed limit" in resp.json()["detail"].lower()

    def test_video_temp_file_cleanup_on_success_and_error(self):
        vid_bytes = _make_sample_video_bytes(duration_frames=10, fps=10.0)
        tmpdir = tempfile.gettempdir()
        before_files = set(os.listdir(tmpdir))

        # Successful video audit
        resp_ok = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("cleanup_ok.mp4", vid_bytes, "video/mp4")},
        )
        assert resp_ok.status_code == 200

        # Erroneous video audit
        resp_err = client.post(
            "/api/v1/hygiene/audit",
            files={"file": ("cleanup_bad.mp4", b"not_valid_video_bytes_xyz", "video/mp4")},
        )
        assert resp_err.status_code == 400

        after_files = set(os.listdir(tmpdir))
        new_files = after_files - before_files
        leaked_mp4s = [f for f in new_files if f.endswith(".mp4")]
        assert len(leaked_mp4s) == 0, f"Leaked temporary video files: {leaked_mp4s}"


# ===========================================================================
# 7. Modular Detector & Unsupported Classes Tests
# ===========================================================================

class MockPPEAndSpillDetector(HygieneDetectorInterface):

    def get_model_id(self) -> str:
        return "mock_yolov8_commercial_kitchen_v1"

    def get_supported_classes(self) -> list[str]:
        return ["protective_gloves", "hairnet", "spill"]

    def detect(self, image: Image.Image) -> list[dict[str, Any]]:
        return [
            {
                "class_name": "protective_gloves",
                "confidence": 0.9125,
                "severity": "Compliant",
                "location": "Food Prep Counter",
                "evidence": "Operator observed with compliant food-grade protective gloves.",
                "recommendation": None,
                "requires_human_review": False,
                "human_review_reason": None,
            },
            {
                "class_name": "spill",
                "confidence": 0.8420,
                "severity": "Minor",
                "location": "Sink Basin Surface",
                "evidence": "Residual liquid accumulation adjacent to washing sink.",
                "recommendation": "Wipe dry with single-use towel.",
                "requires_human_review": False,
                "human_review_reason": None,
            },
        ]


class TestHygieneModularDetector:

    def test_modular_detector_loading_unloading_and_real_confidences(self):
        try:
            # 1. Load mock detector
            detector = MockPPEAndSpillDetector()
            hygiene_model_manager.load_detector(detector)

            # Status check
            resp = client.get("/api/v1/hygiene/status")
            assert resp.status_code == 200
            status_data = resp.json()
            assert status_data["analysis_mode"] == "object_detector"
            assert status_data["model_loaded"] is True
            assert status_data["model_id"] == "mock_yolov8_commercial_kitchen_v1"
            assert status_data["supported_classes"] == ["protective_gloves", "hairnet", "spill"]

            # Audit check
            img_bytes = _make_jpeg_bytes(rgb=(200, 200, 200), size=(200, 200))
            audit_resp = client.post(
                "/api/v1/hygiene/audit",
                files={"file": ("kitchen_station.jpg", img_bytes, "image/jpeg")},
            )
            assert audit_resp.status_code == 200
            audit_data = audit_resp.json()
            assert audit_data["analysis_mode"] == "object_detector"
            assert audit_data["model_id"] == "mock_yolov8_commercial_kitchen_v1"
            assert audit_data["model_loaded"] is True

            # Model produced real confidence values
            indicators = audit_data["observed_indicators"]
            assert len(indicators) == 2
            gloves_ind = [i for i in indicators if "gloves" in i["violation_type"].lower()][0]
            assert gloves_ind["confidence"] == 0.9125

            spill_ind = [i for i in indicators if "spill" in i["violation_type"].lower()][0]
            assert spill_ind["confidence"] == 0.8420
        finally:
            # Cleanly unload
            hygiene_model_manager.unload_detector()

        # Status reverts to heuristic
        resp_revert = client.get("/api/v1/hygiene/status")
        assert resp_revert.json()["analysis_mode"] == "heuristic_visual_cues"
        assert resp_revert.json()["model_loaded"] is False

    def test_unsupported_detection_classes_are_not_invented(self):
        # In heuristic mode, manager only declares supported visual cues
        classes = hygiene_model_manager.supported_classes
        assert "salmonella" not in classes
        assert "microbial_pathogen" not in classes
        assert "internal_temperature" not in classes

        # Test detector that ignores unsupported classes
        class RogueDetector(HygieneDetectorInterface):
            def get_model_id(self) -> str:
                return "rogue_detector"

            def get_supported_classes(self) -> list[str]:
                return ["visible_tray"]

            def detect(self, image: Image.Image) -> list[dict[str, Any]]:
                return [
                    {"class_name": "visible_tray", "confidence": 0.85, "severity": "Compliant"},
                    {"class_name": "salmonella_bacteria", "confidence": 0.99, "severity": "Critical"},
                ]

        audit_res = _detector_hygiene_audit(
            [(Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8)), 0.0)],
            media_type="image",
            detector=RogueDetector(),
        )
        # salmonella_bacteria was ignored because it's not in get_supported_classes()
        class_names = [ind["violation_type"].lower() for ind in audit_res["observed_indicators"]]
        assert not any("salmonella" in c for c in class_names)
        assert any("visible tray" in c for c in class_names)
