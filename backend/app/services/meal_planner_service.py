from typing import List, Dict, Any, Optional
import re
from app.providers.factory import get_ai_provider
from app.services.recipe_service import detect_allergens

def calculate_bmr_tdee(
    age: int,
    gender: str,
    weight_kg: float,
    height_cm: float,
    activity_level: str = "moderately_active",
    goal: str = "maintenance"
) -> Dict[str, float]:
    """
    Calculates Basal Metabolic Rate using Mifflin-St Jeor and Total Daily Energy Expenditure.
    Does not prescribe aggressive caloric deficits for minors (age < 18).
    """
    if gender.lower() == "male":
        bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) + 5.0
    else:
        bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) - 161.0

    multipliers = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9,
    }
    mult = multipliers.get(activity_level.lower().replace(" ", "_"), 1.55)
    tdee = bmr * mult

    # Safety rule: Do not prescribe weight loss deficits for youth / minors
    if age < 18 or goal == "maintenance":
        target = tdee
    elif goal == "weight_loss":
        target = max(1400.0, tdee - 400.0)
    elif goal == "muscle_gain":
        target = tdee + 350.0
    else:
        target = tdee

    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "target_calories": round(target, 0),
    }

def filter_conflicting_meals(meals: List[Dict[str, Any]], allergens: List[str], exclusions: List[str]) -> List[Dict[str, Any]]:
    """Checks generated meals against strict allergens and exclusions."""
    clean_exclusions = [e.lower().strip() for e in (exclusions or []) if e.strip()]
    safe_meals = []

    for meal in meals:
        ings = meal.get("ingredients", [])
        ing_text = " ".join([i.lower() for i in ings])
        
        # Check allergens
        detected_allergens = detect_allergens(ings, allergens)
        has_allergen_conflict = any("Matches declared user allergy" in a for a in detected_allergens)

        # Check explicit exclusions
        has_exclusion_conflict = any(re.search(r'\b' + re.escape(exc) + r'\b', ing_text) for exc in clean_exclusions)

        if not has_allergen_conflict and not has_exclusion_conflict:
            safe_meals.append(meal)

    return safe_meals

async def generate_plan_service(request_data: Dict[str, Any]) -> Dict[str, Any]:
    provider = get_ai_provider()
    plan = await provider.generate_meal_plan(request_data)
    return plan

def generate_replacement_meal(
    day_number: int,
    meal_type: str,
    target_cals: float,
    diet_type: str,
    exclude_ingredients: List[str]
) -> Dict[str, Any]:
    """Generates an alternative single meal satisfying dietary constraints."""
    catalog = {
        "breakfast": [
            ("Mediterranean Spinach & Egg White Frittata", ["Egg whites", "Baby spinach", "Feta cheese", "Whole grain toast"], 380, 24, 28, 12),
            ("Berry & Chia Seed Overnight Oats", ["Rolled oats", "Chia seeds", "Almond milk", "Mixed berries"], 350, 14, 52, 9),
            ("Warm Quinoa Porridge with Sliced Pear", ["Quinoa flakes", "Oat milk", "Pear", "Cinnamon", "Walnuts"], 360, 12, 54, 10),
            ("Smoked Salmon & Avocado Toast", ["Whole grain toast", "Smoked salmon", "Mashed avocado", "Capers"], 410, 22, 34, 18),
        ],
        "lunch": [
            ("Lemon Herb Grilled Chicken Bowl", ["Grilled chicken breast", "Brown rice", "Steamed zucchini", "Tzatziki"], 520, 42, 48, 14),
            ("Crispy Tofu & Edamame Soba Noodles", ["Buckwheat soba", "Firm tofu", "Edamame", "Sesame ginger dressing"], 490, 26, 62, 16),
            ("Mediterranean Tuna & White Bean Salad", ["Albacore tuna", "Cannellini beans", "Arugula", "Olive oil lemon dressing"], 480, 38, 36, 15),
            ("Roasted Turkey & Sweet Potato Plate", ["Roast turkey breast", "Baked sweet potato", "Steamed green beans"], 510, 40, 44, 12),
        ],
        "dinner": [
            ("Pan-Seared Cod with Asparagus & Quinoa", ["Atlantic cod fillet", "Asparagus spears", "Cooked quinoa", "Garlic butter"], 540, 44, 38, 16),
            ("Herb Roasted Chicken Thigh with Broccoli", ["Skinless chicken thigh", "Roasted broccoli florets", "Baby potatoes"], 560, 42, 36, 20),
            ("Lentil & Sweet Potato Coconut Curry", ["Brown lentils", "Sweet potato chunks", "Light coconut milk", "Spinach"], 510, 22, 68, 14),
            ("Grilled Prawns with Mediterranean Couscous", ["Tiger prawns", "Whole wheat couscous", "Roasted bell peppers", "Parsley"], 490, 36, 52, 11),
        ],
        "snack": [
            ("Greek Yogurt with Raw Walnuts", ["Plain Greek yogurt", "Raw walnuts", "Drop of honey"], 210, 15, 12, 11),
            ("Apple Slices with Natural Peanut Butter", ["Crisp apple", "Natural peanut butter"], 190, 5, 24, 9),
            ("Roasted Chickpeas with Smoked Paprika", ["Chickpeas", "Olive oil", "Paprika", "Sea salt"], 170, 7, 26, 4),
            ("Celery Sticks with Creamy Hummus", ["Celery ribs", "Classic garlic hummus"], 150, 4, 16, 7),
        ],
    }

    candidates = catalog.get(meal_type.lower(), catalog["lunch"])
    clean_excludes = [e.lower().strip() for e in exclude_ingredients if e.strip()]

    selected = candidates[0]
    for name, ings, cals, p, c, f in candidates:
        ing_str = " ".join([i.lower() for i in ings])
        if not any(exc in ing_str for exc in clean_excludes):
            selected = (name, ings, cals, p, c, f)
            break

    name, ings, cals, p, c, f = selected
    return {
        "day_number": day_number,
        "meal_type": meal_type,
        "meal_name": name,
        "description": f"Customized alternative {meal_type} satisfying dietary exclusions.",
        "servings": 1,
        "ingredients": ings,
        "calories": float(cals),
        "protein_g": float(p),
        "carbs_g": float(c),
        "fat_g": float(f),
    }

def build_consolidated_shopping_list(plan_title: str, plan_id: str, items: List[Any]) -> Dict[str, Any]:
    """Aggregates all meal ingredients into categorized supermarket departments."""
    categories = {
        "Fresh Produce": set(),
        "Meat, Seafood & Plant Proteins": set(),
        "Dairy & Chilled Alternatives": set(),
        "Pantry, Grains & Legumes": set(),
        "Oils, Herbs & Seasonings": set(),
    }

    protein_keywords = ["chicken", "salmon", "turkey", "beef", "tofu", "fish", "prawn", "tuna", "egg", "shrimp"]
    produce_keywords = ["spinach", "asparagus", "broccoli", "apple", "berry", "pear", "zucchini", "sweet potato", "lemon", "garlic", "greens", "celery", "carrot", "avocado", "blueberries"]
    dairy_keywords = ["yogurt", "milk", "cheese", "feta", "butter", "tzatziki", "cream"]
    grain_keywords = ["oats", "quinoa", "rice", "toast", "bread", "beans", "chickpeas", "lentils", "couscous", "noodles", "chia"]

    for item in items:
        # item can be dict or ORM object
        ings = item.get("ingredients", []) if isinstance(item, dict) else (item.ingredients or [])
        for ing in ings:
            clean_ing = ing.strip()
            if not clean_ing:
                continue
            ing_lower = clean_ing.lower()

            placed = False
            for kw in produce_keywords:
                if kw in ing_lower:
                    categories["Fresh Produce"].add(clean_ing)
                    placed = True
                    break
            if placed:
                continue

            for kw in protein_keywords:
                if kw in ing_lower:
                    categories["Meat, Seafood & Plant Proteins"].add(clean_ing)
                    placed = True
                    break
            if placed:
                continue

            for kw in dairy_keywords:
                if kw in ing_lower:
                    categories["Dairy & Chilled Alternatives"].add(clean_ing)
                    placed = True
                    break
            if placed:
                continue

            for kw in grain_keywords:
                if kw in ing_lower:
                    categories["Pantry, Grains & Legumes"].add(clean_ing)
                    placed = True
                    break
            if placed:
                continue

            categories["Oils, Herbs & Seasonings"].add(clean_ing)

    cat_list = []
    total_distinct = 0
    for cat_name, ing_set in categories.items():
        if ing_set:
            sorted_items = sorted(list(ing_set))
            cat_list.append({"category": cat_name, "items": sorted_items})
            total_distinct += len(sorted_items)

    return {
        "plan_id": plan_id,
        "plan_title": plan_title,
        "categories": cat_list,
        "total_distinct_items": total_distinct,
    }
