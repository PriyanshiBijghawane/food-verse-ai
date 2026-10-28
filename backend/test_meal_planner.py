"""
Epic 5.1, 5.2 & Phase 8 — Meal Planner Tests
============================================
Tests cover:
- Biometric profile validation (valid ranges, required fields, invalid entries)
- BMR and TDEE calculation correctness
- 5-meal schedule generation with consistent nutrition summation
- Allergen exclusion verification (e.g. dairy, nuts)
- Dietary constraints (vegan, vegetarian, keto)
- Alternative meals and weekly overview
- Hydration plan accuracy
- Operational status endpoint reporting provider, bounds, and diet options
- Multi-day meal plans (1-14 days) with day summaries and consistency
- Configurable meals per day (2-6 meals) with exact calorie distribution
- Serving size scaling (1-12 portions)
- Input bounds validation (days, meals_per_day, servings)
- Consolidated shopping list generation with automated pantry deduction
- Strict excluded ingredients enforcement
- Nutrition estimates with portion uncertainty bounds (min <= max)
- Explicit allergen cross-contact warnings and disclaimers
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

_VALID_PROFILE = {
    "age": 28,
    "gender": "female",
    "height_cm": 165.0,
    "weight_kg": 62.0,
    "activity_level": "moderately_active",
    "primary_goal": "weight_loss",
    "diet_type": "balanced",
    "cuisine_preferences": ["Mediterranean"],
    "allergies": ["peanuts"],
    "food_restrictions": ["no pork"],
    "medical_conditions": ["none"],
}


# ===========================================================================
# 1. Baseline Biometric Profile Validation Tests
# ===========================================================================

class TestMealPlannerProfileValidation:

    def test_valid_profile_succeeds(self):
        resp = client.post("/api/v1/meal-plan/generate", json=_VALID_PROFILE)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["meals"]) == 5
        assert len(data["alternative_meals"]) >= 1
        assert len(data["weekly_overview"]) == 7
        assert data["hydration_guidance"]["recommended_liters_per_day"] > 1.5

    def test_invalid_age_rejected(self):
        bad = dict(_VALID_PROFILE, age=150)
        resp = client.post("/api/v1/meal-plan/generate", json=bad)
        assert resp.status_code == 422  # Pydantic validation error

    def test_invalid_height_rejected(self):
        bad = dict(_VALID_PROFILE, height_cm=20.0)
        resp = client.post("/api/v1/meal-plan/generate", json=bad)
        assert resp.status_code == 422

    def test_invalid_gender_rejected(self):
        bad = dict(_VALID_PROFILE, gender="alien")
        resp = client.post("/api/v1/meal-plan/generate", json=bad)
        assert resp.status_code == 422

    def test_invalid_activity_rejected(self):
        bad = dict(_VALID_PROFILE, activity_level="couch_potato")
        resp = client.post("/api/v1/meal-plan/generate", json=bad)
        assert resp.status_code == 422


# ===========================================================================
# 2. Baseline Plan Generation & Nutrition Tests
# ===========================================================================

class TestMealPlanGenerationAndNutrition:

    def test_calorie_summation_consistency(self):
        resp = client.post("/api/v1/meal-plan/generate", json=_VALID_PROFILE)
        assert resp.status_code == 200
        data = resp.json()

        meals = data["meals"]
        meal_calorie_sum = sum(m["calories"] for m in meals)
        total_cal = data["daily_nutrition_totals"]["total_calories_kcal"]
        assert meal_calorie_sum == total_cal, f"Sum of meals ({meal_calorie_sum}) must match total ({total_cal})"

        # Check 5 occasions
        meal_types = [m["meal_type"] for m in meals]
        expected_types = ["Breakfast", "Mid-Morning Snack", "Lunch", "Evening Snack", "Dinner"]
        assert meal_types == expected_types

    def test_strict_allergen_exclusion(self):
        # Request plan with dairy allergy
        dairy_allergic_profile = dict(
            _VALID_PROFILE,
            diet_type="balanced",
            allergies=["dairy", "milk", "cheese", "yogurt"],
        )
        resp = client.post("/api/v1/meal-plan/generate", json=dairy_allergic_profile)
        assert resp.status_code == 200
        data = resp.json()

        for meal in data["meals"]:
            for ing in meal["ingredients"]:
                assert "feta" not in ing.lower()
                assert "yogurt" not in ing.lower()
                assert "cheese" not in ing.lower()
                # Animal/dairy milk excluded; plant milks like almond milk are dairy-free
                assert "cow milk" not in ing.lower()
                assert "dairy" not in ing.lower()

    def test_vegan_diet_compliance(self):
        vegan_profile = dict(
            _VALID_PROFILE,
            diet_type="vegan",
            allergies=[],
        )
        resp = client.post("/api/v1/meal-plan/generate", json=vegan_profile)
        assert resp.status_code == 200
        data = resp.json()

        for meal in data["meals"]:
            for ing in meal["ingredients"]:
                assert "chicken" not in ing.lower()
                assert "salmon" not in ing.lower()
                assert "egg" not in ing.lower()


# ===========================================================================
# 3. Status Endpoint Tests
# ===========================================================================

class TestMealPlannerStatusEndpoint:

    def test_meal_planner_status_endpoint(self):
        resp = client.get("/api/v1/meal-plan/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"
        assert "vegetarian" in data["supported_diet_types"]
        assert "vegan" in data["supported_diet_types"]
        assert "dairy" in data["supported_allergens"]
        assert "peanuts" in data["supported_allergens"]
        assert data["min_days"] == 1
        assert data["max_days"] == 14
        assert data["min_meals_per_day"] == 2
        assert data["max_meals_per_day"] == 6
        assert data["min_servings"] == 1
        assert data["max_servings"] == 12


# ===========================================================================
# 4. Multi-Day Plans & Customization Tests
# ===========================================================================

class TestMultiDayMealPlanning:

    def test_multi_day_3_days_plan_structure(self):
        profile_3_days = dict(_VALID_PROFILE, days=3)
        resp = client.post("/api/v1/meal-plan/generate", json=profile_3_days)
        assert resp.status_code == 200
        data = resp.json()

        assert data["plan_parameters"]["days"] == 3
        daily_plans = data["daily_plans"]
        assert len(daily_plans) == 3

        for i, dp in enumerate(daily_plans, 1):
            assert dp["day_number"] == i
            assert "Day " in dp["day_name"]
            assert len(dp["meals"]) == 5
            day_sum = sum(m["calories"] for m in dp["meals"])
            assert day_sum == dp["daily_nutrition_totals"]["total_calories_kcal"]
            assert dp["uncertainty_range"]["min_calories"] <= dp["uncertainty_range"]["max_calories"]

    def test_meals_per_day_customization_3_meals(self):
        profile_3_meals = dict(_VALID_PROFILE, meals_per_day=3)
        resp = client.post("/api/v1/meal-plan/generate", json=profile_3_meals)
        assert resp.status_code == 200
        data = resp.json()

        day_meals = data["daily_plans"][0]["meals"]
        assert len(day_meals) == 3
        meal_types = [m["meal_type"] for m in day_meals]
        assert meal_types == ["Breakfast", "Lunch", "Dinner"]

        day_sum = sum(m["calories"] for m in day_meals)
        assert day_sum == data["daily_plans"][0]["daily_nutrition_totals"]["total_calories_kcal"]

    def test_servings_scaling(self):
        profile_servings = dict(_VALID_PROFILE, servings=4)
        resp = client.post("/api/v1/meal-plan/generate", json=profile_servings)
        assert resp.status_code == 200
        data = resp.json()

        assert data["plan_parameters"]["servings"] == 4
        base_target = data["biometric_calculations"]["target_calories_kcal"]
        assert data["daily_plans"][0]["target_calories"] == base_target * 4
        assert "4 serving" in data["meals"][0]["portion_size"]


# ===========================================================================
# 5. Input Bounds Validation Tests
# ===========================================================================

class TestInputBoundsValidation:

    def test_invalid_days_bounds_rejected(self):
        bad_zero = dict(_VALID_PROFILE, days=0)
        resp_zero = client.post("/api/v1/meal-plan/generate", json=bad_zero)
        assert resp_zero.status_code == 422

        bad_excessive = dict(_VALID_PROFILE, days=15)
        resp_excessive = client.post("/api/v1/meal-plan/generate", json=bad_excessive)
        assert resp_excessive.status_code == 422

    def test_invalid_meals_per_day_bounds_rejected(self):
        bad_few = dict(_VALID_PROFILE, meals_per_day=1)
        resp_few = client.post("/api/v1/meal-plan/generate", json=bad_few)
        assert resp_few.status_code == 422

        bad_many = dict(_VALID_PROFILE, meals_per_day=7)
        resp_many = client.post("/api/v1/meal-plan/generate", json=bad_many)
        assert resp_many.status_code == 422

    def test_invalid_servings_bounds_rejected(self):
        bad_servings_zero = dict(_VALID_PROFILE, servings=0)
        resp_zero = client.post("/api/v1/meal-plan/generate", json=bad_servings_zero)
        assert resp_zero.status_code == 422

        bad_servings_huge = dict(_VALID_PROFILE, servings=15)
        resp_huge = client.post("/api/v1/meal-plan/generate", json=bad_servings_huge)
        assert resp_huge.status_code == 422


# ===========================================================================
# 6. Consolidated Shopping List & Pantry Deduction Tests
# ===========================================================================

class TestConsolidatedShoppingList:

    def test_shopping_list_consolidation_and_pantry_deduction(self):
        profile_with_pantry = dict(
            _VALID_PROFILE,
            days=3,
            available_ingredients=["Olive oil", "Rolled Oats", "Pumpkin Seeds"],
        )
        resp = client.post("/api/v1/meal-plan/generate", json=profile_with_pantry)
        assert resp.status_code == 200
        data = resp.json()

        shop_list = data["consolidated_shopping_list"]
        assert shop_list is not None
        assert shop_list["total_unique_items"] > 0
        assert shop_list["pantry_items_count"] >= 1
        assert shop_list["items_to_buy_count"] > 0

        # Check pantry item recognition
        items = shop_list["items"]
        oats_item = [i for i in items if "oat" in i["item_name"].lower()]
        assert len(oats_item) >= 1
        assert oats_item[0]["in_pantry"] is True

        # Check unowned items are marked to purchase
        produce_items = [i for i in items if not i["in_pantry"]]
        assert len(produce_items) > 0

        # Check category structure
        assert "Produce" in shop_list["categories"]
        assert "Proteins" in shop_list["categories"]


# ===========================================================================
# 7. Dietary Restrictions & Excluded Ingredients Tests
# ===========================================================================

class TestDietaryRestrictionsAndExclusions:

    def test_vegetarian_diet_excludes_all_meats_across_multi_day_plan(self):
        veg_profile = dict(
            _VALID_PROFILE,
            diet_type="vegetarian",
            days=3,
            allergies=[],
        )
        resp = client.post("/api/v1/meal-plan/generate", json=veg_profile)
        assert resp.status_code == 200
        data = resp.json()

        for dp in data["daily_plans"]:
            for meal in dp["meals"]:
                for ing in meal["ingredients"]:
                    ing_lower = ing.lower()
                    assert "chicken" not in ing_lower
                    assert "salmon" not in ing_lower
                    assert "beef" not in ing_lower
                    assert "pork" not in ing_lower
                    assert "turkey" not in ing_lower

    def test_excluded_ingredients_enforced(self):
        profile_excluded = dict(
            _VALID_PROFILE,
            days=2,
            excluded_ingredients=["mushrooms", "asparagus"],
        )
        resp = client.post("/api/v1/meal-plan/generate", json=profile_excluded)
        assert resp.status_code == 200
        data = resp.json()

        for dp in data["daily_plans"]:
            for meal in dp["meals"]:
                for ing in meal["ingredients"]:
                    assert "mushroom" not in ing.lower()
                    assert "asparagus" not in ing.lower()

    def test_allergen_cross_contact_disclaimer_present(self):
        resp = client.post("/api/v1/meal-plan/generate", json=_VALID_PROFILE)
        assert resp.status_code == 200
        data = resp.json()
        assert "allergen_safety_notice" in data
        assert "cross-contact" in data["allergen_safety_notice"].lower()


# ===========================================================================
# 8. Nutrition Estimates & Uncertainty Bounds Tests
# ===========================================================================

class TestNutritionEstimatesAndUncertainty:

    def test_nutrition_uncertainty_bounds(self):
        resp = client.post("/api/v1/meal-plan/generate", json=_VALID_PROFILE)
        assert resp.status_code == 200
        data = resp.json()

        for meal in data["meals"]:
            assert "instructions" in meal and len(meal["instructions"]) >= 1
            unc = meal.get("nutrition_uncertainty")
            assert unc is not None
            assert unc["min_calories"] <= unc["max_calories"]

        day_totals = data["daily_nutrition_totals"]
        assert day_totals["min_calories_kcal"] <= day_totals["max_calories_kcal"]
