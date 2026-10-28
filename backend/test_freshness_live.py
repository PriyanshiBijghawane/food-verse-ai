import os, io, json
import numpy as np
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_synthetic_fresh_food_live():
    # Create a synthetic fresh food image
    arr = np.zeros((300, 300, 3), dtype=np.uint8)
    arr[:150, :150] = [200, 50, 40]    # red tomato zone
    arr[:150, 150:] = [60, 160, 60]    # green lettuce
    arr[150:, :150] = [160, 100, 60]   # brown bread
    arr[150:, 150:] = [220, 200, 50]   # yellow banana
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    img_data = buf.getvalue()

    resp = client.post(
        "/api/v1/food/freshness?food_hint=mixed+food",
        files={"file": ("test_synthetic.jpg", img_data, "image/jpeg")},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "success"
    assert "freshness_score" in result
    assert "freshness_label" in result
    assert "safety_status" in result
    assert "detected_signs" in result
    assert result["food_category"] in ("cooked", "generic")


if __name__ == "__main__":
    test_synthetic_fresh_food_live()
    print("test_synthetic_fresh_food_live passed!")

