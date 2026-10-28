from typing import Dict, Any, Optional
import sys
import os

# Ensure backend root is on path to import nutrition_data
backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from nutrition_data import lookup_nutrition_data, get_nutrition_estimate, FOOD_NUTRITION_DATASET

def calculate_nutritional_score(
    calories: Optional[float],
    protein_g: Optional[float],
    fiber_g: Optional[float],
    sodium_mg: Optional[float]
) -> tuple[Optional[float], Optional[str]]:
    """
    Computes an informational nutrient density heuristic score (1.0 to 10.0).
    Documented Formula:
      Score = base 5.0 + (protein density bonus) + (fiber bonus) - (sodium penalty)
    Bounded between 1.0 and 10.0.
    """
    if calories is None or calories <= 0:
        return None, "Nutritional score unavailable due to missing caloric baseline."

    score = 5.0

    # Protein density factor: up to +2.5 pts
    if protein_g is not None:
        protein_cals = protein_g * 4.0
        protein_ratio = protein_cals / calories
        score += min(2.5, protein_ratio * 7.0)

    # Fiber factor: up to +2.5 pts
    if fiber_g is not None:
        score += min(2.5, (fiber_g / 10.0) * 2.5)

    # Sodium factor: up to -2.0 pts if high sodium
    if sodium_mg is not None and sodium_mg > 600:
        penalty = min(2.0, ((sodium_mg - 600) / 1000.0) * 2.0)
        score -= penalty

    clamped = round(min(10.0, max(1.0, score)), 1)
    explanation = (
        f"Informational Nutrient Density Score ({clamped}/10): Derived from protein density "
        f"({protein_g or 'unknown'}g) and dietary fiber ({fiber_g or 'unknown'}g) relative to total energy ({calories} kcal) "
        "and sodium load. Note: This heuristic is informational only and does not represent an individualized medical dietary prescription."
    )
    return clamped, explanation

def get_portion_scaled_nutrition(
    food_name: str,
    target_grams: float = 100.0,
    unit: str = "grams"
) -> Dict[str, Any]:
    """
    Looks up verified reference facts and scales linearly to target portion weight.
    Preserves None for unmeasured micronutrients rather than falsely reporting zero.
    """
    norm_name = food_name.lower().strip().replace(" ", "_").replace("-", "_")
    base_data = None

    if norm_name in FOOD_NUTRITION_DATASET:
        base_data = FOOD_NUTRITION_DATASET[norm_name]
    else:
        verified = lookup_nutrition_data(food_name)
        if verified:
            base_data = verified

    if not base_data:
        # Fallback to general estimate or unknown
        est = get_nutrition_estimate(food_name)
        base_data = est

    # Standard reference baseline is assumed 100g if not parsed
    base_grams = 100.0
    serving_str = str(base_data.get("serving_size", "100g"))
    if "g)" in serving_str:
        try:
            part = serving_str.split("g)")[0].split("approx.")[-1].strip()
            base_grams = float(part)
        except Exception:
            base_grams = 100.0

    scale_factor = target_grams / base_grams if base_grams > 0 else 1.0

    cals = base_data.get("calories")
    prot = base_data.get("protein_g")
    carbs = base_data.get("carbs_g")
    fat = base_data.get("fat_g")
    fiber = base_data.get("fiber_g")
    sodium = base_data.get("sodium_mg")

    scaled_cals = round(cals * scale_factor, 1) if cals is not None else None
    scaled_prot = round(prot * scale_factor, 1) if prot is not None else None
    scaled_carbs = round(carbs * scale_factor, 1) if carbs is not None else None
    scaled_fat = round(fat * scale_factor, 1) if fat is not None else None
    scaled_fiber = round(fiber * scale_factor, 1) if fiber is not None else None
    scaled_sodium = round(sodium * scale_factor, 1) if sodium is not None else None

    score, explanation = calculate_nutritional_score(scaled_cals, scaled_prot, scaled_fiber, scaled_sodium)

    return {
        "food_name": base_data.get("food_name", food_name.title()),
        "portion_grams": target_grams,
        "portion_unit": unit,
        "calories": scaled_cals,
        "protein_g": scaled_prot,
        "carbs_g": scaled_carbs,
        "fat_g": scaled_fat,
        "fiber_g": scaled_fiber,
        "sodium_mg": scaled_sodium,
        "nutritional_score": score,
        "score_explanation": explanation,
        "provenance": "USDA FoodData Central reference scaling",
    }
