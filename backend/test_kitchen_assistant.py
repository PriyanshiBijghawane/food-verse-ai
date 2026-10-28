"""
Epic 4.2 & Phase 7 — Smart Kitchen Recipe Generator Tests
=========================================================
Tests cover:
- Recipe generation from text ingredients
- Recipe generation with image upload
- Rejection of empty submissions (neither text nor image)
- Rejection of invalid image uploads
- Operational status endpoint reporting provider and constraints
- Vegetarian dietary restriction strict enforcement (no meat, auto-substitutions)
- Vegan dietary preferences and dairy substitutions
- Servings and cooking-time bounds validation (1-20 servings, 5-360 min)
- Long input rejection (> 1000 characters)
- Verified USDA / FDA food safety guidance separation and disclaimers
- Transparent fallback disclosure (rule_based_fallback vs llm_generated)
- Mocked LLM provider success handling
- Mocked LLM provider timeout, rate limit (429), and malformed response recovery
- Prevention of secret / API key leakage in responses
"""

import io
import json
import os
from unittest.mock import AsyncMock, patch

import httpx
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _make_jpeg_bytes() -> bytes:
    arr = np.zeros((200, 200, 3), dtype=np.uint8)
    arr[:, :] = [180, 60, 40]
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ===========================================================================
# 1. Baseline Ingestion & Generation Tests
# ===========================================================================

class TestKitchenAssistant:

    def test_text_ingredients_recipe_generation(self):
        resp = client.post(
            "/api/v1/cooking/assistant",
            data={
                "ingredients": "pasta, tomatoes, garlic, basil, olive oil",
                "dietary_preference": "vegetarian",
                "cuisine": "Italian",
                "max_time_minutes": 25,
                "skill_level": "Easy",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "dish_name" in data and len(data["dish_name"]) > 0
        assert len(data["ingredients"]) >= 3
        assert len(data["instructions"]) >= 2
        assert "timer_minutes" in data["instructions"][0]
        assert data["nutrition_estimates"]["calories"] > 0
        assert data["nutrition_estimates"]["protein_g"] >= 0
        assert "storage_tips" in data
        assert any("Vegetarian" in t or "vegetarian" in t.lower() for t in data["dietary_tags"])

    def test_image_and_text_recipe_generation(self):
        img_bytes = _make_jpeg_bytes()
        resp = client.post(
            "/api/v1/cooking/assistant",
            data={
                "ingredients": "spinach, mushrooms",
                "cuisine": "Mediterranean",
            },
            files={"image": ("fridge_ingredients.jpg", img_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["detected_from_image"]) >= 1
        assert len(data["ingredients"]) >= 2

    def test_empty_request_rejected(self):
        resp = client.post(
            "/api/v1/cooking/assistant",
            data={"ingredients": "   "},
        )
        assert resp.status_code == 400
        assert "provide ingredient descriptions or upload a photo" in resp.json()["detail"].lower()

    def test_invalid_image_format_rejected(self):
        resp = client.post(
            "/api/v1/cooking/assistant",
            data={"ingredients": "chicken"},
            files={"image": ("bad.txt", b"plain text", "text/plain")},
        )
        assert resp.status_code == 400
        assert "Invalid image format" in resp.json()["detail"]


# ===========================================================================
# 2. Operational Status Endpoint Tests
# ===========================================================================

class TestCookingStatusEndpoint:

    def test_cooking_status_endpoint_returns_metadata(self):
        resp = client.get("/api/v1/cooking/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"
        assert "llm_provider" in data
        assert "active_model_id" in data
        assert data["fallback_engine"] == "deterministic_culinary_engine_v1"
        assert "vegetarian" in data["supported_dietary_options"]
        assert "vegan" in data["supported_dietary_options"]
        assert data["max_servings"] == 20
        assert data["max_cooking_time_minutes"] == 360
        assert "USDA_FDA" in data["food_safety_database_version"]


# ===========================================================================
# 3. Dietary Restrictions & Vegetarian Enforcement Tests
# ===========================================================================

class TestDietaryRestrictionsAndVegetarianAdaptation:

    def test_vegetarian_strict_exclusion_and_replacement(self):
        # User provides chicken along with a vegetarian preference
        resp = client.post(
            "/api/v1/cooking/assistant",
            data={
                "ingredients": "chicken, basmati rice, onions, ginger, turmeric",
                "dietary_preference": "vegetarian",
                "cuisine": "Indian",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert any("vegetarian" in t.lower() for t in data["dietary_tags"])

        # Dish name should not celebrate chicken
        assert "Chicken" not in data["dish_name"]

        # Ingredients must not list plain chicken; must provide a vegetarian replacement
        ing_names = [i["name"].lower() for i in data["ingredients"]]
        assert not any(i == "chicken" or "chicken breast" in i for i in ing_names)
        assert any("tofu" in i or "paneer" in i for i in ing_names)

        # Substitutions array must explain the conversion
        subs = data.get("substitutions", [])
        assert any("chicken" in s["original"].lower() for s in subs)

    def test_vegan_dietary_preference_and_substitutions(self):
        resp = client.post(
            "/api/v1/cooking/assistant",
            data={
                "ingredients": "pasta, tomatoes, cheese, olive oil",
                "dietary_preference": "vegan",
                "cuisine": "Italian",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert any("vegan" in t.lower() for t in data["dietary_tags"])
        # Cheese should have a vegan substitution listed
        subs = data.get("substitutions", [])
        assert any("cheese" in s["original"].lower() or "parmesan" in s["original"].lower() for s in subs)


# ===========================================================================
# 4. Input Validation & Bounds Tests
# ===========================================================================

class TestInputValidationAndBounds:

    def test_servings_input_and_bounds(self):
        # Valid serving size
        resp_ok = client.post(
            "/api/v1/cooking/assistant",
            data={"ingredients": "eggs, bread", "servings": 4},
        )
        assert resp_ok.status_code == 200
        assert resp_ok.json()["servings"] == 4

        # Zero servings rejected
        resp_zero = client.post(
            "/api/v1/cooking/assistant",
            data={"ingredients": "eggs, bread", "servings": 0},
        )
        assert resp_zero.status_code == 400
        assert "serving count must be between" in resp_zero.json()["detail"].lower()

        # Excessive servings (> 20) rejected
        resp_huge = client.post(
            "/api/v1/cooking/assistant",
            data={"ingredients": "eggs, bread", "servings": 25},
        )
        assert resp_huge.status_code == 400
        assert "serving count must be between" in resp_huge.json()["detail"].lower()

    def test_cook_time_bounds_validation(self):
        # Time too short (< 5 min)
        resp_short = client.post(
            "/api/v1/cooking/assistant",
            data={"ingredients": "rice, beans", "max_time_minutes": 2},
        )
        assert resp_short.status_code == 400
        assert "cooking time must be between" in resp_short.json()["detail"].lower()

        # Time too long (> 360 min)
        resp_long = client.post(
            "/api/v1/cooking/assistant",
            data={"ingredients": "rice, beans", "max_time_minutes": 500},
        )
        assert resp_long.status_code == 400
        assert "cooking time must be between" in resp_long.json()["detail"].lower()

    def test_excessive_ingredient_length_rejected(self):
        long_text = "tomato, " * 200  # > 1000 characters
        resp = client.post(
            "/api/v1/cooking/assistant",
            data={"ingredients": long_text},
        )
        assert resp.status_code == 400
        assert "exceeds maximum allowed length" in resp.json()["detail"].lower()


# ===========================================================================
# 5. Food Safety Guidance Separation Tests
# ===========================================================================

class TestFoodSafetyGuidance:

    def test_verified_food_safety_guidance_present(self):
        resp = client.post(
            "/api/v1/cooking/assistant",
            data={"ingredients": "chicken breast, sweet potato"},
        )
        assert resp.status_code == 200
        data = resp.json()

        # Safety guidance must be distinct, non-empty, and ground in USDA standards
        safety = data.get("food_safety_guidance", [])
        assert isinstance(safety, list)
        assert len(safety) >= 3

        safety_text = " ".join(safety).lower()
        # Must include poultry minimum temperature (165°F or 74°C)
        assert "165°f" in safety_text or "74°c" in safety_text
        # Must include cross-contamination and safe storage rules
        assert "cross-contamination" in safety_text
        assert "danger zone" in safety_text or "40°f" in safety_text

        # Disclaimer must state approximations
        assert "disclaimer" in data


# ===========================================================================
# 6. Fallback Disclosure Tests
# ===========================================================================

class TestFallbackDisclosure:

    def test_fallback_disclosure_when_no_api_key(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        resp = client.post(
            "/api/v1/cooking/assistant",
            data={"ingredients": "pasta, garlic, olive oil"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["engine_mode"] == "rule_based_fallback"
        assert data["model_id"] == "deterministic_culinary_engine_v1"
        assert "Rule-Based Fallback" in data["generation_engine"]
        assert "Not produced by generative AI" in data["generation_disclosure"]


# ===========================================================================
# 7. Mocked LLM Provider Integration Tests
# ===========================================================================

class TestMockedLLMProvider:

    @pytest.mark.anyio
    async def test_mocked_groq_llm_success(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "gsk_test_mock_valid_key_123")

        mock_recipe = {
            "dish_name": "Truffle Scented Mushroom Risotto",
            "summary": "Decadent arborio rice gently stirred with wild forest mushrooms.",
            "prep_time": "10 mins",
            "cook_time": "20 mins",
            "total_time": "30 mins",
            "servings": 2,
            "difficulty": "Medium",
            "cuisine": "Italian",
            "dietary_tags": ["Vegetarian"],
            "ingredients": [
                {"name": "Arborio Rice", "quantity": "200g", "notes": "High starch"},
                {"name": "Wild Mushrooms", "quantity": "150g", "notes": "Sliced"},
            ],
            "instructions": [
                {"step": 1, "title": "Toast Grain", "instruction": "Toast rice until translucent.", "timer_minutes": 3, "chef_tip": "Keep stirring"},
                {"step": 2, "title": "Ladle Stock", "instruction": "Add warm broth ladle by ladle.", "timer_minutes": 17, "chef_tip": "Continuous gentle heat"},
            ],
            "nutrition_estimates": {"calories": 410, "protein_g": 9.5, "carbs_g": 68.0, "fat_g": 11.0, "fiber_g": 3.0},
            "substitutions": [],
            "storage_tips": "Best eaten freshly plated.",
        }

        mock_resp = httpx.Response(
            status_code=200,
            json={
                "choices": [{
                    "message": {
                        "content": json.dumps(mock_recipe)
                    }
                }]
            },
            request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        )

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            resp = client.post(
                "/api/v1/cooking/assistant",
                data={"ingredients": "rice, mushrooms, garlic"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["engine_mode"] == "llm_generated"
            assert "llama-3.3-70b-versatile" in data["model_id"]
            assert data["dish_name"] == "Truffle Scented Mushroom Risotto"
            assert len(data["food_safety_guidance"]) >= 2

    @pytest.mark.anyio
    async def test_mocked_llm_provider_timeout_triggers_fallback(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "gsk_test_mock_valid_key_123")

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Read timed out after 20.0s")

            resp = client.post(
                "/api/v1/cooking/assistant",
                data={"ingredients": "spinach, eggs"},
            )
            assert resp.status_code == 200
            data = resp.json()
            # Must gracefully fall back to local rule-based culinary engine
            assert data["engine_mode"] == "rule_based_fallback"
            assert data["model_id"] == "deterministic_culinary_engine_v1"

    @pytest.mark.anyio
    async def test_mocked_llm_provider_rate_limit_triggers_fallback(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "gsk_test_mock_valid_key_123")

        mock_err_resp = httpx.Response(
            status_code=429,
            text='{"error": {"message": "Rate limit exceeded"}}',
            request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        )

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_err_resp

            resp = client.post(
                "/api/v1/cooking/assistant",
                data={"ingredients": "pasta, tomatoes"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["engine_mode"] == "rule_based_fallback"
            assert data["model_id"] == "deterministic_culinary_engine_v1"

    @pytest.mark.anyio
    async def test_mocked_llm_malformed_json_triggers_fallback(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "gsk_test_mock_valid_key_123")

        mock_malformed = httpx.Response(
            status_code=200,
            json={
                "choices": [{
                    "message": {
                        "content": "Here is a recipe: not valid json at all!"
                    }
                }]
            },
            request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        )

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_malformed

            resp = client.post(
                "/api/v1/cooking/assistant",
                data={"ingredients": "pasta, tomatoes"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["engine_mode"] == "rule_based_fallback"
            assert data["model_id"] == "deterministic_culinary_engine_v1"

    def test_api_secrets_never_exposed_in_response(self, monkeypatch):
        secret_token = "gsk_super_secret_production_token_xyz987"
        monkeypatch.setenv("GROQ_API_KEY", secret_token)

        resp = client.post(
            "/api/v1/cooking/assistant",
            data={"ingredients": "pasta, tomatoes"},
        )
        assert resp.status_code == 200
        raw_json_str = resp.text
        assert secret_token not in raw_json_str
