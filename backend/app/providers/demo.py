from typing import Dict, Any, List, Optional, Tuple
from app.providers.base import BaseAIProvider

class DemoAIProvider(BaseAIProvider):
    """
    Deterministic demo provider supplying verified, realistic fixtures for testing and evaluation
    without requiring external cloud AI credentials or billing.
    """
    @property
    def provider_name(self) -> str:
        return "demo"

    @property
    def execution_mode(self) -> str:
        return "demo"

    async def analyze_food_image(
        self, image_bytes: bytes, description: Optional[str] = None
    ) -> Dict[str, Any]:
        food_label = description.strip() if description and description.strip() else "Mediterranean Salmon Bowl"
        return {
            "food_name": food_label,
            "candidate_foods": [
                {"label": "Mediterranean Salmon Bowl", "confidence": 0.88, "region": "Primary Plate"},
                {"label": "Steamed Quinoa & Greens", "confidence": 0.74, "region": "Base Grain"},
                {"label": "Roasted Cherry Tomatoes", "confidence": 0.65, "region": "Garnish Side"},
            ],
            "confidence": 0.88,
            "portion_grams": 350.0,
            "portion_unit": "grams",
            "calories": 520.0,
            "protein_g": 38.0,
            "carbs_g": 42.0,
            "fat_g": 22.0,
            "fiber_g": 7.0,
            "sodium_mg": 480.0,
            "nutritional_score": 8.5,
            "score_explanation": "Informational Nutrient Density Score (0-10): Calculated via protein-to-calorie ratio, dietary fiber content, and healthy fats. Not a clinical prescription.",
            "uncertainty_notes": "Portions estimated from visual perspective assuming standard 26cm dining plate. Cooking oils and sodium seasoning cannot be directly measured from imagery.",
            "detected_items": [
                {"name": "Baked Salmon Fillet", "portion_grams": 150.0, "calories": 280.0, "protein_g": 31.0},
                {"name": "Cooked Quinoa", "portion_grams": 120.0, "calories": 145.0, "protein_g": 5.0},
                {"name": "Baby Spinach & Veggies", "portion_grams": 80.0, "calories": 95.0, "protein_g": 2.0},
            ],
            "provenance": "demo_fixture",
            "execution_mode": "demo",
            "provider": "demo",
            "model_id": "demo-food-v1",
        }

    async def assess_visible_freshness(
        self, image_bytes: bytes, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        food_type = context.get("food_type", "Produce item")
        storage = context.get("storage_method", "refrigerated")
        odor = context.get("reported_odor_change", False)

        if odor:
            category = "possible_visible_spoilage"
            obs = [
                "User-reported off-odor detected; odor is a primary microbiological spoilage indicator.",
                "Surface displays early softening and dulling of natural hue.",
            ]
            steps = [
                "Inspect under clean lighting for mold filaments or slime layers.",
                "Do not taste or sample if an abnormal odor is present.",
                "Discard if texture is slimy or off-odor is sharp.",
            ]
        else:
            category = "no_obvious_visible_spoilage"
            obs = [
                "Surface pigmentation shows uniform coloration without active mold colonies.",
                "Skin / rind integrity appears intact without extensive soft rot or visible leakage.",
                "No visible bacterial slime or mycelial growth observed on exposed surfaces.",
            ]
            steps = [
                f"Maintain verified {storage} temperature (4°C / 40°F or lower).",
                "Wash thoroughly with potable running water before food preparation.",
                "Use within standard recommended household storage window.",
            ]

        return {
            "food_type": food_type,
            "spoilage_category": category,
            "category_label": category.replace("_", " ").title(),
            "visual_observations": obs,
            "storage_context": context,
            "limitations": "Surface visual observation cannot detect invisible bacterial pathogens (Salmonella, Listeria, E. coli) or tasteless toxins. Microscopic bacterial growth precedes visible decay.",
            "conservative_next_steps": steps,
            "execution_mode": "demo",
            "provider": "demo",
            "model_id": "demo-freshness-v1",
        }

    async def analyze_kitchen_image(
        self, image_bytes: bytes, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "media_type": "image",
            "checklist_score": 85.0,
            "score_formula": "Observational Checklist Score: Base 100 - (15 pts * Critical) - (10 pts * Moderate) - (5 pts * Minor). Sampled visual checklist only.",
            "findings": [
                {
                    "area": "Food Contact Surfaces",
                    "observation": "Stainless prep surface clean and wiped down; no visible debris or standing liquid.",
                    "severity": "info",
                    "corrective_action": "Maintain scheduled sanitizing wipe cycles with calibrated sanitizer solution.",
                },
                {
                    "area": "Food Storage Separation",
                    "observation": "Covered plastic containers labeled in upper refrigeration shelf; no direct raw meat drip risk visible.",
                    "severity": "info",
                    "corrective_action": "Verify internal walk-in thermometer log is recorded twice daily.",
                },
                {
                    "area": "Visible Waste Accumulation",
                    "observation": "Trash receptacle partially filled near prep station; lid is open.",
                    "severity": "minor",
                    "corrective_action": "Keep waste receptacle covered when not in active deposit to minimize pest attractants.",
                },
            ],
            "unobservable_items": [
                "Internal chemical sanitizer PPM concentration (requires chemical test strip)",
                "Internal food probe temperatures (requires calibrated stem thermometer)",
                "Pest activity in unlit floor voids or baseboards",
            ],
            "execution_mode": "demo",
            "provider": "demo",
            "model_id": "demo-hygiene-v1",
        }

    async def analyze_video_frames(
        self, frames: List[Tuple[float, bytes]]
    ) -> Dict[str, Any]:
        return {
            "media_type": "video",
            "frames_analyzed": len(frames),
            "checklist_score": 80.0,
            "score_formula": "Observational Checklist Score: Base 100 - (15 pts * Critical) - (10 pts * Moderate) - (5 pts * Minor) averaged across sampled frames.",
            "findings": [
                {
                    "area": "Protective Clothing & PPE",
                    "observation": "Kitchen prep personnel observed wearing hair restraints and aprons at 1.5s.",
                    "severity": "info",
                    "corrective_action": "Continue enforcement of hygienic outerwear standards.",
                    "timestamp_seconds": 1.5,
                },
                {
                    "area": "Potential Raw-to-Ready Contact",
                    "observation": "Cutting board station at 4.2s shows raw poultry prep; vegetable prep occurs on separate green board.",
                    "severity": "info",
                    "corrective_action": "Sanitize board and wash hands for 20 seconds before switching stations.",
                    "timestamp_seconds": 4.2,
                },
                {
                    "area": "Liquid Spills & Waste",
                    "observation": "Small liquid splash observed near handwash sink at 7.0s.",
                    "severity": "minor",
                    "corrective_action": "Mop and dry floor promptly to eliminate slip hazard and bacterial growth.",
                    "timestamp_seconds": 7.0,
                },
            ],
            "unobservable_items": [
                "Continuous 24/7 video surveillance (only sampled key frames evaluated)",
                "Handwashing water temperature (>100°F / 38°C)",
                "Dishwashing machine final rinse temperature (>180°F / 82°C)",
            ],
            "execution_mode": "demo",
            "provider": "demo",
            "model_id": "demo-video-hygiene-v1",
        }

    async def generate_recipe(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        ingredients = request_data.get("ingredients", ["chicken breast", "spinach", "garlic", "olive oil"])
        cuisine = request_data.get("cuisine_preference", "Mediterranean")
        time_mins = request_data.get("cooking_time_minutes", 30)
        
        return {
            "title": f"Pan-Seared Herb Chicken with Garlic Sauteed Spinach",
            "description": f"A vibrant {cuisine}-style weeknight dinner featuring tender seasoned chicken breast paired with quick-wilted leafy spinach and aromatic garlic.",
            "ingredients": [
                {"name": "Chicken Breast", "quantity": "2", "unit": "boneless fillets (approx 350g)", "optional": False},
                {"name": "Fresh Baby Spinach", "quantity": "200", "unit": "grams", "optional": False},
                {"name": "Garlic Cloves", "quantity": "3", "unit": "minced", "optional": False},
                {"name": "Extra Virgin Olive Oil", "quantity": "2", "unit": "tablespoons", "optional": False},
                {"name": "Lemon", "quantity": "1", "unit": "juiced", "optional": True},
                {"name": "Dried Oregano & Thyme", "quantity": "1", "unit": "teaspoon", "optional": False},
                {"name": "Kosher Salt & Black Pepper", "quantity": "0.5", "unit": "teaspoon each", "optional": False},
            ],
            "servings": 2,
            "prep_time_minutes": 10,
            "cook_time_minutes": min(time_mins - 10, 20),
            "instructions": [
                {"step": 1, "instruction": "Pat chicken breasts dry with clean paper towels. Season both sides evenly with oregano, thyme, salt, and freshly cracked black pepper.", "timer_minutes": None},
                {"step": 2, "instruction": "Heat 1 tablespoon olive oil in a heavy skillet over medium-high heat until shimmering.", "timer_minutes": 2},
                {"step": 3, "instruction": "Add chicken breasts to skillet. Sear undisturbed for 6-7 minutes until a golden crust develops, then flip.", "timer_minutes": 7},
                {"step": 4, "instruction": "Cook the second side for 5-6 minutes until internal temperature reaches a verified 74°C (165°F). Transfer to a warm plate to rest.", "timer_minutes": 6},
                {"step": 5, "instruction": "In the same skillet, reduce heat to medium. Add remaining olive oil and minced garlic; sauté for 30 seconds until fragrant.", "timer_minutes": 1},
                {"step": 6, "instruction": "Toss in fresh baby spinach and cook for 2 minutes until just wilted. Finish with a squeeze of fresh lemon juice.", "timer_minutes": 2},
                {"step": 7, "instruction": "Slice chicken and serve immediately alongside the warm garlic spinach.", "timer_minutes": None},
            ],
            "substitutions": [
                {"original": "Chicken Breast", "alternative": "Firm Tofu or Boneless Salmon fillet"},
                {"original": "Fresh Baby Spinach", "alternative": "Kale, Swiss Chard, or Arugula"},
                {"original": "Olive Oil", "alternative": "Avocado oil or unsalted butter"},
            ],
            "storage_guidance": "Cool leftovers within 2 hours. Store in an airtight container refrigerated at <=4°C for up to 3 days.",
            "nutrition_estimates": {
                "calories_per_serving": 340,
                "protein_g": 36.0,
                "carbs_g": 6.0,
                "fat_g": 18.0,
                "fiber_g": 3.0,
                "sodium_mg": 380,
                "provenance": "USDA reference calculation",
            },
            "allergen_warnings": [],
            "execution_mode": "demo",
            "provider": "demo",
        }

    async def generate_meal_plan(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        target_cals = request_data.get("target_calories") or 2000.0
        diet = request_data.get("diet_type", "balanced")
        
        days_count = 7 if request_data.get("plan_type") == "7_day" else 1
        items = []

        day_templates = [
            ("Overnight Chia Oats with Berries", "Grilled Chicken Quinoa Bowl", "Baked Herb Salmon with Asparagus", "Greek Yogurt with Walnuts"),
            ("Avocado Toast with Poached Egg", "Turkey Avocado Wrap", "Stir-Fried Tofu with Mixed Vegetables", "Apple with Almond Butter"),
            ("Berry Protein Smoothie Bowl", "Lentil Vegetable Soup with Crusty Bread", "Lean Beef Meatballs with Zucchini Noodles", "Hummus with Cucumber Slices"),
            ("Greek Scramble with Feta and Spinach", "Mediterranean Tuna Salad", "Roasted Chicken Breast with Sweet Potato", "Mixed Roasted Nuts"),
            ("Oatmeal with Sliced Banana and Cinnamon", "Chickpea and Quinoa Salad", "Pan-Seared White Fish with Steamed Broccoli", "Edamame Pods with Sea Salt"),
            ("Whole Grain Waffles with Blueberries", "Warm Black Bean Soup", "Turkey Chili with Brown Rice", "Carrot Sticks with Guacamole"),
            ("Shakshuka with Whole Grain Toast", "Cottage Cheese Fruit Bowl", "Grilled Prawn Skewers with Couscous", "Dark Chocolate & Almonds"),
        ]

        for day in range(1, days_count + 1):
            idx = (day - 1) % len(day_templates)
            b_name, l_name, d_name, s_name = day_templates[idx]

            items.extend([
                {
                    "day_number": day,
                    "meal_type": "breakfast",
                    "meal_name": b_name,
                    "description": "Nutrient-dense morning meal rich in complex carbs and lean proteins.",
                    "servings": 1,
                    "ingredients": ["Oats", "Chia seeds", "Almond milk", "Blueberries", "Honey"],
                    "calories": round(target_cals * 0.25, 0),
                    "protein_g": 18.0,
                    "carbs_g": 48.0,
                    "fat_g": 10.0,
                },
                {
                    "day_number": day,
                    "meal_type": "lunch",
                    "meal_name": l_name,
                    "description": "Sustained-energy midday meal with balanced fiber and healthy fats.",
                    "servings": 1,
                    "ingredients": ["Quinoa", "Chicken or Plant Protein", "Mixed Greens", "Olive Oil Dressing"],
                    "calories": round(target_cals * 0.35, 0),
                    "protein_g": 35.0,
                    "carbs_g": 52.0,
                    "fat_g": 16.0,
                },
                {
                    "day_number": day,
                    "meal_type": "dinner",
                    "meal_name": d_name,
                    "description": "Restorative evening dinner promoting muscle recovery and satiety.",
                    "servings": 1,
                    "ingredients": ["Salmon or Protein Alternative", "Asparagus", "Lemon", "Garlic"],
                    "calories": round(target_cals * 0.30, 0),
                    "protein_g": 38.0,
                    "carbs_g": 26.0,
                    "fat_g": 18.0,
                },
                {
                    "day_number": day,
                    "meal_type": "snack",
                    "meal_name": s_name,
                    "description": "Light wholesome snack to stabilize blood sugar.",
                    "servings": 1,
                    "ingredients": ["Greek Yogurt", "Walnuts", "Cinnamon"],
                    "calories": round(target_cals * 0.10, 0),
                    "protein_g": 12.0,
                    "carbs_g": 14.0,
                    "fat_g": 6.0,
                },
            ])

        return {
            "title": f"Personalized 7-Day {diet.title()} Nutrition Plan",
            "plan_type": request_data.get("plan_type", "7_day"),
            "daily_target_calories": target_cals,
            "diet_type": diet,
            "total_estimated_calories": target_cals * days_count,
            "total_protein_g": 103.0 * days_count,
            "total_carbs_g": 140.0 * days_count,
            "total_fat_g": 50.0 * days_count,
            "allergen_notes": ["Zero blacklisted allergens detected across all 7 days of scheduled meals."],
            "execution_mode": "demo",
            "items": items,
        }

    async def transcribe_audio(
        self, audio_bytes: bytes
    ) -> Dict[str, Any]:
        return {
            "transcript": "Generate a high-protein dinner recipe with chicken breast, garlic, and fresh spinach under 30 minutes.",
            "confidence": 0.96,
            "audio_duration_seconds": 4.5,
            "fallback_note": "Demo fixture: Transcribed query simulating clear English speech.",
        }
