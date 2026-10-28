from typing import List, Dict, Any, Optional
import re
from app.providers.factory import get_ai_provider

COMMON_ALLERGENS = {
    "dairy": ["milk", "cheese", "butter", "cream", "yogurt", "ghee", "casein", "whey"],
    "eggs": ["egg", "eggs", "mayonnaise", "albumen"],
    "peanuts": ["peanut", "peanuts", "peanut butter", "groundnut"],
    "tree_nuts": ["almond", "walnut", "cashew", "pecan", "pistachio", "hazelnut", "macadamia"],
    "gluten": ["wheat", "flour", "bread", "pasta", "barley", "rye", "couscous", "soy sauce"],
    "soy": ["soy", "soya", "tofu", "edamame", "tempeh", "miso"],
    "fish": ["salmon", "tuna", "cod", "halibut", "tilapia", "anchovy", "fish"],
    "shellfish": ["shrimp", "prawn", "crab", "lobster", "clam", "mussel", "oyster", "scallop"],
    "sesame": ["sesame", "tahini"],
}

def detect_allergens(ingredients: List[str], user_allergies: Optional[List[str]] = None) -> List[str]:
    """
    Deterministic allergen checking over ingredient list.
    Flags known top food allergens and checks user-declared allergies.
    """
    detected = set()
    user_lower = [a.lower().strip() for a in (user_allergies or [])]

    for ing in ingredients:
        ing_lower = ing.lower()
        for allergen_group, keywords in COMMON_ALLERGENS.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', ing_lower):
                    detected.add(f"Contains {allergen_group.replace('_', ' ').title()} ({kw})")

        # Check explicit user allergies with singular/plural support
        for user_a in user_lower:
            if not user_a:
                continue
            stem = user_a.rstrip("s")
            if re.search(r'\b' + re.escape(user_a) + r'\b', ing_lower) or (len(stem) > 3 and re.search(r'\b' + re.escape(stem), ing_lower)):
                detected.add(f"Matches declared user allergy: {user_a.title()}")

    return sorted(list(detected))

async def generate_recipe_service(request_data: Dict[str, Any]) -> Dict[str, Any]:
    provider = get_ai_provider()
    recipe = await provider.generate_recipe(request_data)

    # Perform deterministic allergen detection across both generated and input ingredients
    ing_names = [i.get("name", "") if isinstance(i, dict) else str(i) for i in recipe.get("ingredients", [])]
    req_ings = [str(x) for x in request_data.get("ingredients", [])]
    detected_allergens = detect_allergens(list(set(ing_names + req_ings)), request_data.get("allergies"))

    recipe["allergen_warnings"] = detected_allergens
    return recipe
