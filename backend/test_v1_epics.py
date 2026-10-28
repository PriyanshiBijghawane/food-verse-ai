import os
import io
import pytest
from fastapi.testclient import TestClient
from main import app
from app.db.session import SessionLocal, init_db
from app.models.entities import User, UploadedAsset, AnalysisJob, MealPlan, MealPlanItem
from app.services.recipe_service import detect_allergens
from app.services.meal_planner_service import (
    calculate_bmr_tdee,
    generate_replacement_meal,
    build_consolidated_shopping_list,
    filter_conflicting_meals,
)
from app.services.nutrition_service import (
    calculate_nutritional_score,
    get_portion_scaled_nutrition,
)
from app.providers.demo import DemoAIProvider
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()
    yield

# ---------------------------------------------------------------------------
# 1. Health & Capabilities Tests
# ---------------------------------------------------------------------------
def test_health_endpoints():
    res1 = client.get("/health")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "ok"
    assert "ai_mode" in data1

    res2 = client.get("/api/v1/health")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "ok"

def test_capabilities_endpoint():
    res = client.get("/api/v1/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert "ai_mode" in data
    assert "supported_features" in data
    assert data["supported_features"]["food_recognition"] is True
    assert data["supported_features"]["kitchen_hygiene_video"] is True
    assert "disclaimers" in data
    assert "visual_limits" in data["disclaimers"]

# ---------------------------------------------------------------------------
# 2. Authentication & Ownership Tests
# ---------------------------------------------------------------------------
def test_password_hashing():
    pw = "SuperSecretPassword123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_flow():
    payload = {"sub": "user-12345", "email": "test@foodverse.ai"}
    token = create_access_token(payload, expires_delta_seconds=3600)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user-12345"
    assert decoded["email"] == "test@foodverse.ai"

def test_auth_register_and_login():
    email = "chef_tester_2026@foodverse.ai"
    password = "SafePassword987!"

    # Register
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": "Chef Tester"}
    )
    # 200 or 400 if already exists in test run
    if reg_res.status_code == 200:
        data = reg_res.json()
        assert "access_token" in data
        assert data["email"] == email

    # Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    token = token_data["access_token"]
    assert token is not None

    # Get Me with token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == email

# ---------------------------------------------------------------------------
# 3. Upload Validation & Security Tests
# ---------------------------------------------------------------------------
def test_upload_empty_file_rejected():
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    res = client.post("/api/v1/uploads", files=files)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

def test_upload_valid_image():
    # Minimal 64x64 valid JPEG bytes
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color=(100, 150, 200)).save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("test_plate.jpg", buf.getvalue(), "image/jpeg")}
    res = client.post("/api/v1/uploads", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert data["media_type"] == "image"
    assert data["mime_type"] == "image/jpeg"

# ---------------------------------------------------------------------------
# 4. Food Portion Scaling & Unknown Nutrient Preservation
# ---------------------------------------------------------------------------
def test_food_portion_scaling_and_score():
    # 100g pizza vs 200g pizza
    scaled_100 = get_portion_scaled_nutrition("pizza", target_grams=100.0)
    scaled_200 = get_portion_scaled_nutrition("pizza", target_grams=200.0)

    assert scaled_100["portion_grams"] == 100.0
    assert scaled_200["portion_grams"] == 200.0
    if scaled_100["calories"] is not None and scaled_200["calories"] is not None:
        assert scaled_200["calories"] == pytest.approx(scaled_100["calories"] * 2.0, rel=0.05)

    assert "score_explanation" in scaled_100
    assert scaled_100["nutritional_score"] is not None
    assert 1.0 <= scaled_100["nutritional_score"] <= 10.0

def test_unknown_nutrients_preserved_as_none():
    score, expl = calculate_nutritional_score(calories=None, protein_g=None, fiber_g=None, sodium_mg=None)
    assert score is None
    assert "unavailable" in expl.lower()

# ---------------------------------------------------------------------------
# 5. Freshness Safety Wording & Categories
# ---------------------------------------------------------------------------
def test_freshness_categories_and_disclaimer():
    res = client.post(
        "/api/v1/freshness/analyze",
        data={
            "food_type": "fresh_spinach",
            "storage_method": "refrigerated",
            "reported_odor_change": "false",
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["spoilage_category"] in {
        "no_obvious_visible_spoilage",
        "possible_visible_spoilage",
        "visible_spoilage_observed",
        "insufficient_information",
    }
    assert "safety_disclaimer" in data
    assert "microbiological" in data["safety_disclaimer"].lower()
    assert "limitations" in data
    assert len(data["conservative_next_steps"]) > 0

# ---------------------------------------------------------------------------
# 6. Hygiene Observational Scoring & Video Job Flow
# ---------------------------------------------------------------------------
def test_hygiene_observational_scoring():
    res = client.post("/api/v1/hygiene/analyze", data={"notes": "Prep line"})
    assert res.status_code == 200
    data = res.json()
    assert 0.0 <= data["checklist_score"] <= 100.0
    assert "score_formula" in data
    assert "non_certification_disclaimer" in data
    assert "certify" in data["non_certification_disclaimer"].lower()
    assert len(data["findings"]) > 0

def test_video_job_status_transitions():
    db = SessionLocal()
    # Create test job
    job = AnalysisJob(
        user_id="test-user-id",
        job_type="video_hygiene",
        status="queued",
        progress_percent=10,
        execution_mode="demo",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Poll job status
    poll_res = client.get(f"/api/v1/jobs/{job.id}")
    assert poll_res.status_code == 200
    pdata = poll_res.json()
    assert pdata["job_id"] == job.id
    assert pdata["status"] == "queued"
    assert pdata["progress_percent"] == 10

    # Simulate transition to processing
    job.status = "processing"
    job.progress_percent = 50
    db.commit()

    poll_res2 = client.get(f"/api/v1/jobs/{job.id}")
    assert poll_res2.json()["status"] == "processing"
    assert poll_res2.json()["progress_percent"] == 50

    db.close()

# ---------------------------------------------------------------------------
# 7. Allergen Detection & Recipe Generation
# ---------------------------------------------------------------------------
def test_deterministic_allergen_checks():
    ingredients = ["1 cup cow milk", "2 tbsp peanut butter", "1 fillet Atlantic salmon"]
    allergens = detect_allergens(ingredients, user_allergies=["peanuts"])
    assert any("Dairy" in a for a in allergens)
    assert any("Peanuts" in a for a in allergens)
    assert any("Fish" in a for a in allergens)
    assert any("Matches declared user allergy" in a for a in allergens)

def test_recipe_generation_with_allergens():
    res = client.post(
        "/api/v1/recipes/generate",
        json={
            "ingredients": ["chicken breast", "spinach", "garlic", "butter"],
            "cuisine_preference": "French",
            "allergies": ["dairy"]
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "title" in data
    assert len(data["instructions"]) > 0
    assert "allergen_warnings" in data
    # Butter contains dairy, so it should be flagged
    assert any("Dairy" in w or "dairy" in w.lower() for w in data["allergen_warnings"])

# ---------------------------------------------------------------------------
# 8. Meal Planner, Single-Meal Replacement & Shopping List
# ---------------------------------------------------------------------------
def test_metabolic_bmr_calculations():
    # Adult female
    res_female = calculate_bmr_tdee(age=28, gender="female", weight_kg=65.0, height_cm=168.0, goal="weight_loss")
    assert res_female["bmr"] > 1300
    assert res_female["target_calories"] >= 1400  # safety floor

    # Minor safety check (age < 18): should not have aggressive deficit
    res_minor = calculate_bmr_tdee(age=15, gender="male", weight_kg=60.0, height_cm=170.0, goal="weight_loss")
    assert res_minor["target_calories"] == round(res_minor["tdee"], 0)  # deficit denied for youth safety

def test_meal_plan_replace_single_meal_and_shopping_list():
    # Generate 7-day plan
    plan_res = client.post(
        "/api/v1/meal-plans",
        json={
            "plan_type": "7_day",
            "target_calories": 2000.0,
            "diet_type": "balanced",
            "allergies": ["peanuts"],
        }
    )
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    plan_id = plan_data["id"]
    assert len(plan_data["items"]) == 28  # 7 days * 4 meals

    # Replace Day 2 Lunch
    rep_res = client.post(
        f"/api/v1/meal-plans/{plan_id}/replace-meal",
        json={
            "day_number": 2,
            "meal_type": "lunch",
            "exclude_ingredients": ["shrimp", "seafood"]
        }
    )
    assert rep_res.status_code == 200
    updated_plan = rep_res.json()
    day2_lunch = next(m for m in updated_plan["items"] if m["day_number"] == 2 and m["meal_type"] == "lunch")
    assert day2_lunch is not None
    assert updated_plan["total_estimated_calories"] > 0

    # Fetch Consolidated Shopping List
    shop_res = client.get(f"/api/v1/meal-plans/{plan_id}/shopping-list")
    assert shop_res.status_code == 200
    shop_data = shop_res.json()
    assert shop_data["plan_id"] == plan_id
    assert len(shop_data["categories"]) > 0
    assert shop_data["total_distinct_items"] > 0

# ---------------------------------------------------------------------------
# 9. History Retrieval and Deletion
# ---------------------------------------------------------------------------
def test_history_and_deletion():
    # History listing
    hist_res = client.get("/api/v1/history")
    assert hist_res.status_code == 200
    items = hist_res.json()
    assert isinstance(items, list)

    # Create dummy food analysis to delete
    food_res = client.post("/api/v1/food/analyze", data={"food_description": "Apple Tart", "portion_grams": 120})
    assert food_res.status_code == 200
    item_id = food_res.json()["id"]

    # Delete item
    del_res = client.delete(f"/api/v1/history/{item_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Confirm deletion
    del_again = client.delete(f"/api/v1/history/{item_id}")
    assert del_again.status_code == 404
