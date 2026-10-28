"""
Epic 2 — Food Recognition & Nutrition Regression Tests
======================================================
Tests verify that Epic 2 nutrition and food recognition routes
remain fully functional and do not regress.
"""

from fastapi.testclient import TestClient
import main
from main import app
from nutrition_data import get_nutrition_estimate

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "model_ready" in data


def test_health_endpoint_metadata():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["application_status"] == "healthy"
    assert "model_ready" in data
    assert "device" in data
    assert data["device"] in ("cpu", "cuda")
    assert data["model_id"] == "nateraw/food"


def test_frontend_dev_origin_is_allowed_by_cors():
    resp = client.options(
        "/api/v1/food/recognize",
        headers={
            "Origin": "http://localhost:5174",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5174"


def test_health_when_model_unavailable():
    original_ready = main._model_ready
    original_error = main._model_error
    main._model_ready = False
    main._model_error = "Simulated offline network timeout during model load"
    try:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["application_status"] == "healthy"
        assert data["model_ready"] is False
        assert "Simulated offline" in data["model_error"]
        assert data["device"] in ("cpu", "cuda")
    finally:
        main._model_ready = original_ready
        main._model_error = original_error


def test_recognize_when_model_unavailable_returns_503():
    original_ready = main._model_ready
    original_error = main._model_error
    original_model = main._model
    main._model_ready = False
    main._model = None
    main._model_error = "Model weights not downloaded."
    try:
        resp = client.post(
            "/api/v1/food/recognize",
            files={"file": ("food.jpg", b"fake-jpeg-bytes", "image/jpeg")},
        )
        assert resp.status_code == 503
        assert "Model is not available" in resp.json()["detail"]
        assert "Model weights not downloaded." in resp.json()["detail"]
    finally:
        main._model_ready = original_ready
        main._model_error = original_error
        main._model = original_model


def test_recognize_rejects_uploads_over_configured_limit(monkeypatch):
    original_ready = main._model_ready
    main._model_ready = True
    monkeypatch.setattr(main.settings, "MAX_UPLOAD_MB", 1)
    try:
        resp = client.post(
            "/api/v1/food/recognize",
            files={"file": ("large.jpg", b"x" * (1024 * 1024 + 1), "image/jpeg")},
        )
        assert resp.status_code == 413
        assert "maximum upload size of 1 MB" in resp.json()["detail"]
    finally:
        main._model_ready = original_ready


def test_nutrition_lookup():
    resp = client.get("/api/v1/food/nutrition?food=pizza")
    assert resp.status_code == 200
    data = resp.json()
    assert "calories" in data
    assert "protein_g" in data
    assert "carbs_g" in data
    assert "fat_g" in data
    assert data["calories"] > 0
    assert "serving_size" in data


def test_nutrition_data_fallback():
    data = get_nutrition_estimate("unknown_exotic_dish_xyz")
    assert "calories" in data
    assert "protein_g" in data
    assert "carbs_g" in data
    assert "fat_g" in data


def test_recognize_invalid_content_type():
    # Set model ready flag for test verification
    original_ready = main._model_ready
    main._model_ready = True
    try:
        resp = client.post(
            "/api/v1/food/recognize",
            files={"file": ("notes.txt", b"just some text", "text/plain")},
        )
        assert resp.status_code == 400
        assert "Invalid file type" in resp.json()["detail"]
    finally:
        main._model_ready = original_ready


def test_recognize_corrupt_image():
    original_ready = main._model_ready
    main._model_ready = True
    try:
        resp = client.post(
            "/api/v1/food/recognize",
            files={"file": ("corrupt.jpg", b"bad_image_binary_data", "image/jpeg")},
        )
        assert resp.status_code == 400
    finally:
        main._model_ready = original_ready


# ---------------------------------------------------------------------------
# Phase 3 Tests: Nutrition Query, Confidence Tiers, Uncertainty, Preprocessing
# ---------------------------------------------------------------------------

def test_nutrition_text_query_apple():
    resp = client.get("/api/v1/food/nutrition?query=apple")
    assert resp.status_code == 200
    data = resp.json()
    assert data["food_name"] == "Fresh Apple"
    assert data["calories"] == 95
    assert data["min_calories"] <= data["max_calories"]
    assert data["min_calories"] == 76
    assert data["max_calories"] == 119
    assert data["is_verified"] is True
    assert "serving_assumptions" in data
    assert "portion_uncertainty_note" in data


def test_nutrition_text_query_banana():
    resp = client.get("/api/v1/food/nutrition?query=banana")
    assert resp.status_code == 200
    data = resp.json()
    assert "Banana" in data["food_name"]
    assert data["calories"] == 105
    assert data["min_calories"] <= data["max_calories"]
    assert data["is_verified"] is True


def test_nutrition_query_unsupported_returns_404():
    resp = client.get("/api/v1/food/nutrition?query=cosmic_dark_matter_xyz_123")
    assert resp.status_code == 404
    detail = resp.json()["detail"].lower()
    assert "not found" in detail
    assert "speculative estimates are not fabricated" in detail


def test_nutrition_missing_query_returns_400():
    resp = client.get("/api/v1/food/nutrition")
    assert resp.status_code == 400
    assert "Please specify a food item" in resp.json()["detail"]


def test_portion_uncertainty_invariants():
    for item in ["pizza", "apple", "chicken_breast", "unknown_custom_item"]:
        data = get_nutrition_estimate(item)
        assert "min_calories" in data
        assert "max_calories" in data
        assert data["min_calories"] <= data["max_calories"]
        assert data["min_calories"] >= 0
        assert "serving_assumptions" in data
        assert "portion_uncertainty_note" in data


def test_image_preprocessing_pipeline_and_no_autocontrast():
    import numpy as np
    from PIL import Image
    from main import preprocess_image

    # Create synthetic natural colored image
    arr = np.full((120, 160, 3), [180, 100, 50], dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    processed_img, meta = preprocess_image(img)

    assert meta["exif_transposed"] is True
    assert meta["contrast_enhanced"] is False
    assert meta["original_resolution"] == "160x120"
    assert "natural" in meta["lighting_notes"].lower()


def test_recognize_low_confidence_rejection_and_tiers():
    import numpy as np
    from PIL import Image
    import io

    # Synthetic non-food / geometric noise image (should result in low confidence < 0.30)
    arr = np.zeros((300, 300, 3), dtype=np.uint8)
    arr[:150, :150] = [200, 50, 40]
    arr[:150, 150:] = [60, 160, 60]
    arr[150:, :150] = [160, 100, 60]
    arr[150:, 150:] = [220, 200, 50]
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    img_bytes = buf.getvalue()

    with TestClient(app) as test_client:
        resp = test_client.post(
            "/api/v1/food/recognize",
            files={"file": ("synthetic_plate.jpg", img_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200
        res = resp.json()
        assert "confidence_tier" in res
        assert res["confidence_tier"] in ("high", "moderate", "low")
        assert "top_5" in res
        assert len(res["top_5"]) == 5

        # On this noise/synthetic image, model confidence is ~0.0368 (< 0.30)
        if res["confidence"] < 0.30:
            assert res["confidence_tier"] == "low"
            assert res["is_uncertain"] is True
            assert res["predicted_label"] == "Uncertain / Unsupported Food"
            assert "candidate_label" in res
            assert "Food-101" in res["confidence_note"]
            assert "nutrition" in res
            assert "reliability_warning" in res["nutrition"]
