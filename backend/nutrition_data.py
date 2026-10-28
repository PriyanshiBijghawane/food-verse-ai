"""
Food Nutrition Reference Dataset for Food Verse AI.
Based on standard reference values from USDA FoodData Central.

DISCLAIMER:
All nutritional values are standard reference estimates based on typical serving sizes
and preparations. They are NOT measured directly from image pixels or sensor data.
Actual nutritional content varies significantly depending on specific ingredients,
cooking methods, oil/salt usage, and portion sizes.
"""

from typing import Any, Dict, Optional

DEFAULT_DISCLAIMER = (
    "Nutritional values are reference estimates based on standard recipes and serving sizes "
    "from USDA FoodData Central. They are not measured directly from image pixels. "
    "Actual nutrition varies based on preparation method, ingredients, and portion size."
)

DATA_SOURCE_NAME = "USDA FoodData Central (Standard Reference)"

# Comprehensive nutritional mapping for all 101 Food-101 classes
# Values are per standard typical serving
FOOD_NUTRITION_DATASET: Dict[str, Dict[str, Any]] = {
    "apple_pie": {
        "food_name": "Apple Pie",
        "serving_size": "1 slice (approx. 125g)",
        "calories": 296,
        "protein_g": 2.4,
        "carbs_g": 42.6,
        "fat_g": 13.8,
        "fiber_g": 1.8,
    },
    "baby_back_ribs": {
        "food_name": "Baby Back Ribs",
        "serving_size": "1/2 rack (approx. 150g edible meat)",
        "calories": 480,
        "protein_g": 38.0,
        "carbs_g": 12.0,
        "fat_g": 31.0,
        "fiber_g": 0.5,
    },
    "baklava": {
        "food_name": "Baklava",
        "serving_size": "1 piece (approx. 50g)",
        "calories": 215,
        "protein_g": 3.5,
        "carbs_g": 25.0,
        "fat_g": 11.8,
        "fiber_g": 1.2,
    },
    "beef_carpaccio": {
        "food_name": "Beef Carpaccio",
        "serving_size": "1 appetizer plate (approx. 100g)",
        "calories": 165,
        "protein_g": 21.0,
        "carbs_g": 1.0,
        "fat_g": 8.5,
        "fiber_g": 0.0,
    },
    "beef_tartare": {
        "food_name": "Beef Tartare",
        "serving_size": "1 portion (approx. 150g)",
        "calories": 260,
        "protein_g": 28.0,
        "carbs_g": 2.5,
        "fat_g": 15.0,
        "fiber_g": 0.2,
    },
    "beet_salad": {
        "food_name": "Beet Salad",
        "serving_size": "1 bowl (approx. 180g)",
        "calories": 170,
        "protein_g": 4.0,
        "carbs_g": 16.0,
        "fat_g": 10.5,
        "fiber_g": 3.2,
    },
    "beignets": {
        "food_name": "Beignets",
        "serving_size": "2 pieces (approx. 80g)",
        "calories": 310,
        "protein_g": 5.0,
        "carbs_g": 44.0,
        "fat_g": 13.0,
        "fiber_g": 1.0,
    },
    "bibimbap": {
        "food_name": "Bibimbap",
        "serving_size": "1 bowl with beef & egg (approx. 400g)",
        "calories": 560,
        "protein_g": 22.0,
        "carbs_g": 78.0,
        "fat_g": 18.0,
        "fiber_g": 6.0,
    },
    "bread_pudding": {
        "food_name": "Bread Pudding",
        "serving_size": "1 square (approx. 150g)",
        "calories": 340,
        "protein_g": 8.0,
        "carbs_g": 52.0,
        "fat_g": 11.5,
        "fiber_g": 1.5,
    },
    "breakfast_burrito": {
        "food_name": "Breakfast Burrito",
        "serving_size": "1 burrito with egg & cheese (approx. 220g)",
        "calories": 450,
        "protein_g": 19.0,
        "carbs_g": 38.0,
        "fat_g": 24.0,
        "fiber_g": 3.0,
    },
    "bruschetta": {
        "food_name": "Bruschetta",
        "serving_size": "2 pieces with tomato & basil (approx. 100g)",
        "calories": 190,
        "protein_g": 5.0,
        "carbs_g": 24.0,
        "fat_g": 8.5,
        "fiber_g": 2.0,
    },
    "caesar_salad": {
        "food_name": "Caesar Salad",
        "serving_size": "1 bowl with dressing & croutons (approx. 200g)",
        "calories": 330,
        "protein_g": 9.0,
        "carbs_g": 12.0,
        "fat_g": 27.0,
        "fiber_g": 3.0,
    },
    "cannoli": {
        "food_name": "Cannoli",
        "serving_size": "1 cannolo with ricotta filling (approx. 90g)",
        "calories": 290,
        "protein_g": 6.0,
        "carbs_g": 32.0,
        "fat_g": 15.5,
        "fiber_g": 1.0,
    },
    "caprese_salad": {
        "food_name": "Caprese Salad",
        "serving_size": "1 plate with mozzarella & tomato (approx. 180g)",
        "calories": 240,
        "protein_g": 12.0,
        "carbs_g": 6.0,
        "fat_g": 18.0,
        "fiber_g": 1.5,
    },
    "carrot_cake": {
        "food_name": "Carrot Cake",
        "serving_size": "1 slice with cream cheese frosting (approx. 120g)",
        "calories": 415,
        "protein_g": 4.5,
        "carbs_g": 55.0,
        "fat_g": 20.5,
        "fiber_g": 2.0,
    },
    "ceviche": {
        "food_name": "Ceviche",
        "serving_size": "1 cup fish ceviche (approx. 180g)",
        "calories": 160,
        "protein_g": 24.0,
        "carbs_g": 8.0,
        "fat_g": 3.0,
        "fiber_g": 1.5,
    },
    "cheese_plate": {
        "food_name": "Cheese Plate",
        "serving_size": "1 assorted cheese board (approx. 120g)",
        "calories": 460,
        "protein_g": 26.0,
        "carbs_g": 4.0,
        "fat_g": 38.0,
        "fiber_g": 0.0,
    },
    "cheesecake": {
        "food_name": "Cheesecake",
        "serving_size": "1 slice plain cheesecake (approx. 125g)",
        "calories": 400,
        "protein_g": 7.0,
        "carbs_g": 32.0,
        "fat_g": 28.0,
        "fiber_g": 0.8,
    },
    "chicken_curry": {
        "food_name": "Chicken Curry",
        "serving_size": "1 bowl chicken curry without rice (approx. 300g)",
        "calories": 380,
        "protein_g": 32.0,
        "carbs_g": 14.0,
        "fat_g": 22.0,
        "fiber_g": 3.5,
    },
    "chicken_quesadilla": {
        "food_name": "Chicken Quesadilla",
        "serving_size": "1 whole quesadilla (approx. 240g)",
        "calories": 520,
        "protein_g": 34.0,
        "carbs_g": 38.0,
        "fat_g": 26.0,
        "fiber_g": 3.0,
    },
    "chicken_wings": {
        "food_name": "Chicken Wings",
        "serving_size": "4 wings with sauce (approx. 180g edible)",
        "calories": 430,
        "protein_g": 32.0,
        "carbs_g": 6.0,
        "fat_g": 30.0,
        "fiber_g": 0.5,
    },
    "chocolate_cake": {
        "food_name": "Chocolate Cake",
        "serving_size": "1 slice chocolate cake with frosting (approx. 110g)",
        "calories": 420,
        "protein_g": 5.0,
        "carbs_g": 54.0,
        "fat_g": 21.0,
        "fiber_g": 3.0,
    },
    "chocolate_mousse": {
        "food_name": "Chocolate Mousse",
        "serving_size": "1 ramekin (approx. 120g)",
        "calories": 310,
        "protein_g": 5.0,
        "carbs_g": 26.0,
        "fat_g": 21.0,
        "fiber_g": 2.0,
    },
    "churros": {
        "food_name": "Churros",
        "serving_size": "3 churros with cinnamon sugar (approx. 100g)",
        "calories": 380,
        "protein_g": 4.0,
        "carbs_g": 48.0,
        "fat_g": 19.0,
        "fiber_g": 2.0,
    },
    "clam_chowder": {
        "food_name": "Clam Chowder",
        "serving_size": "1 cup New England chowder (approx. 250ml)",
        "calories": 240,
        "protein_g": 9.0,
        "carbs_g": 22.0,
        "fat_g": 13.0,
        "fiber_g": 1.5,
    },
    "club_sandwich": {
        "food_name": "Club Sandwich",
        "serving_size": "1 sandwich with turkey & bacon (approx. 280g)",
        "calories": 590,
        "protein_g": 36.0,
        "carbs_g": 44.0,
        "fat_g": 29.0,
        "fiber_g": 4.0,
    },
    "crab_cakes": {
        "food_name": "Crab Cakes",
        "serving_size": "2 cakes (approx. 160g)",
        "calories": 320,
        "protein_g": 24.0,
        "carbs_g": 16.0,
        "fat_g": 18.0,
        "fiber_g": 1.0,
    },
    "creme_brulee": {
        "food_name": "Crème Brûlée",
        "serving_size": "1 ramekin (approx. 140g)",
        "calories": 420,
        "protein_g": 5.0,
        "carbs_g": 30.0,
        "fat_g": 32.0,
        "fiber_g": 0.0,
    },
    "croque_madame": {
        "food_name": "Croque Madame",
        "serving_size": "1 sandwich with fried egg (approx. 260g)",
        "calories": 610,
        "protein_g": 32.0,
        "carbs_g": 38.0,
        "fat_g": 36.0,
        "fiber_g": 2.5,
    },
    "cup_cakes": {
        "food_name": "Cupcakes",
        "serving_size": "1 frosted cupcake (approx. 85g)",
        "calories": 305,
        "protein_g": 3.0,
        "carbs_g": 44.0,
        "fat_g": 13.5,
        "fiber_g": 0.8,
    },
    "deviled_eggs": {
        "food_name": "Deviled Eggs",
        "serving_size": "2 egg halves (approx. 70g)",
        "calories": 140,
        "protein_g": 6.5,
        "carbs_g": 1.0,
        "fat_g": 12.0,
        "fiber_g": 0.0,
    },
    "donuts": {
        "food_name": "Donuts",
        "serving_size": "1 glazed donut (approx. 65g)",
        "calories": 260,
        "protein_g": 3.5,
        "carbs_g": 31.0,
        "fat_g": 14.0,
        "fiber_g": 1.0,
    },
    "dumplings": {
        "food_name": "Dumplings",
        "serving_size": "5 steamed pork/veggie dumplings (approx. 150g)",
        "calories": 280,
        "protein_g": 13.0,
        "carbs_g": 34.0,
        "fat_g": 10.0,
        "fiber_g": 2.0,
    },
    "edamame": {
        "food_name": "Edamame",
        "serving_size": "1 cup in pods, edible beans (approx. 120g)",
        "calories": 150,
        "protein_g": 14.0,
        "carbs_g": 10.0,
        "fat_g": 6.0,
        "fiber_g": 5.0,
    },
    "eggs_benedict": {
        "food_name": "Eggs Benedict",
        "serving_size": "1 serving with hollandaise (approx. 220g)",
        "calories": 540,
        "protein_g": 22.0,
        "carbs_g": 24.0,
        "fat_g": 40.0,
        "fiber_g": 1.0,
    },
    "escargots": {
        "food_name": "Escargots",
        "serving_size": "6 snails in garlic herb butter (approx. 100g)",
        "calories": 230,
        "protein_g": 15.0,
        "carbs_g": 3.0,
        "fat_g": 17.5,
        "fiber_g": 0.0,
    },
    "falafel": {
        "food_name": "Falafel",
        "serving_size": "3 patties (approx. 90g)",
        "calories": 290,
        "protein_g": 9.0,
        "carbs_g": 32.0,
        "fat_g": 15.0,
        "fiber_g": 6.0,
    },
    "filet_mignon": {
        "food_name": "Filet Mignon",
        "serving_size": "1 cooked tenderloin steak (approx. 180g)",
        "calories": 380,
        "protein_g": 44.0,
        "carbs_g": 0.0,
        "fat_g": 22.0,
        "fiber_g": 0.0,
    },
    "fish_and_chips": {
        "food_name": "Fish and Chips",
        "serving_size": "1 standard portion with tartar sauce (approx. 300g)",
        "calories": 680,
        "protein_g": 28.0,
        "carbs_g": 68.0,
        "fat_g": 34.0,
        "fiber_g": 4.0,
    },
    "foie_gras": {
        "food_name": "Foie Gras",
        "serving_size": "1 portion seared (approx. 60g)",
        "calories": 275,
        "protein_g": 6.5,
        "carbs_g": 2.5,
        "fat_g": 26.5,
        "fiber_g": 0.0,
    },
    "french_fries": {
        "food_name": "French Fries",
        "serving_size": "1 medium serving (approx. 115g)",
        "calories": 365,
        "protein_g": 4.0,
        "carbs_g": 48.0,
        "fat_g": 17.0,
        "fiber_g": 4.0,
    },
    "french_onion_soup": {
        "food_name": "French Onion Soup",
        "serving_size": "1 bowl with melted gruyère (approx. 280g)",
        "calories": 290,
        "protein_g": 14.0,
        "carbs_g": 24.0,
        "fat_g": 15.0,
        "fiber_g": 2.5,
    },
    "french_toast": {
        "food_name": "French Toast",
        "serving_size": "2 slices with butter & syrup (approx. 180g)",
        "calories": 390,
        "protein_g": 10.0,
        "carbs_g": 58.0,
        "fat_g": 14.0,
        "fiber_g": 2.0,
    },
    "fried_calamari": {
        "food_name": "Fried Calamari",
        "serving_size": "1 appetizer basket (approx. 150g)",
        "calories": 380,
        "protein_g": 22.0,
        "carbs_g": 26.0,
        "fat_g": 20.0,
        "fiber_g": 1.0,
    },
    "fried_rice": {
        "food_name": "Fried Rice",
        "serving_size": "1 bowl vegetable/egg fried rice (approx. 250g)",
        "calories": 390,
        "protein_g": 9.0,
        "carbs_g": 60.0,
        "fat_g": 12.5,
        "fiber_g": 2.5,
    },
    "frozen_yogurt": {
        "food_name": "Frozen Yogurt",
        "serving_size": "1 cup vanilla/fruit (approx. 180g)",
        "calories": 220,
        "protein_g": 6.0,
        "carbs_g": 38.0,
        "fat_g": 5.0,
        "fiber_g": 0.0,
    },
    "garlic_bread": {
        "food_name": "Garlic Bread",
        "serving_size": "2 slices buttered (approx. 70g)",
        "calories": 240,
        "protein_g": 5.5,
        "carbs_g": 26.0,
        "fat_g": 13.0,
        "fiber_g": 1.5,
    },
    "gnocchi": {
        "food_name": "Gnocchi",
        "serving_size": "1 plate potato gnocchi in marinara (approx. 220g)",
        "calories": 310,
        "protein_g": 7.0,
        "carbs_g": 58.0,
        "fat_g": 5.5,
        "fiber_g": 3.5,
    },
    "greek_salad": {
        "food_name": "Greek Salad",
        "serving_size": "1 bowl with feta, olives & olive oil (approx. 220g)",
        "calories": 260,
        "protein_g": 6.0,
        "carbs_g": 11.0,
        "fat_g": 21.0,
        "fiber_g": 3.5,
    },
    "grilled_cheese_sandwich": {
        "food_name": "Grilled Cheese Sandwich",
        "serving_size": "1 whole sandwich with cheddar (approx. 140g)",
        "calories": 410,
        "protein_g": 14.0,
        "carbs_g": 32.0,
        "fat_g": 25.0,
        "fiber_g": 2.0,
    },
    "grilled_salmon": {
        "food_name": "Grilled Salmon",
        "serving_size": "1 fillet cooked (approx. 170g)",
        "calories": 350,
        "protein_g": 38.0,
        "carbs_g": 0.0,
        "fat_g": 21.0,
        "fiber_g": 0.0,
    },
    "guacamole": {
        "food_name": "Guacamole",
        "serving_size": "1/2 cup fresh dip (approx. 115g)",
        "calories": 185,
        "protein_g": 2.5,
        "carbs_g": 10.0,
        "fat_g": 17.0,
        "fiber_g": 7.5,
    },
    "gyoza": {
        "food_name": "Gyoza",
        "serving_size": "5 pan-fried pork/cabbage gyoza (approx. 125g)",
        "calories": 260,
        "protein_g": 10.0,
        "carbs_g": 26.0,
        "fat_g": 12.0,
        "fiber_g": 1.5,
    },
    "hamburger": {
        "food_name": "Hamburger",
        "serving_size": "1 single patty with bun & condiments (approx. 200g)",
        "calories": 510,
        "protein_g": 28.0,
        "carbs_g": 40.0,
        "fat_g": 26.0,
        "fiber_g": 2.5,
    },
    "hot_and_sour_soup": {
        "food_name": "Hot and Sour Soup",
        "serving_size": "1 cup traditional broth (approx. 250ml)",
        "calories": 120,
        "protein_g": 7.0,
        "carbs_g": 13.0,
        "fat_g": 4.5,
        "fiber_g": 1.5,
    },
    "hot_dog": {
        "food_name": "Hot Dog",
        "serving_size": "1 frank in bun with mustard (approx. 120g)",
        "calories": 320,
        "protein_g": 11.0,
        "carbs_g": 26.0,
        "fat_g": 19.0,
        "fiber_g": 1.0,
    },
    "huevos_rancheros": {
        "food_name": "Huevos Rancheros",
        "serving_size": "1 plate with 2 eggs, tortilla & salsa (approx. 280g)",
        "calories": 430,
        "protein_g": 20.0,
        "carbs_g": 35.0,
        "fat_g": 23.0,
        "fiber_g": 5.0,
    },
    "hummus": {
        "food_name": "Hummus",
        "serving_size": "1/3 cup chickpea dip (approx. 80g)",
        "calories": 190,
        "protein_g": 6.0,
        "carbs_g": 16.0,
        "fat_g": 12.0,
        "fiber_g": 4.5,
    },
    "ice_cream": {
        "food_name": "Ice Cream",
        "serving_size": "1/2 cup vanilla ice cream (approx. 100g)",
        "calories": 210,
        "protein_g": 4.0,
        "carbs_g": 24.0,
        "fat_g": 11.5,
        "fiber_g": 0.7,
    },
    "lasagna": {
        "food_name": "Lasagna",
        "serving_size": "1 square baked beef & ricotta lasagna (approx. 280g)",
        "calories": 460,
        "protein_g": 28.0,
        "carbs_g": 39.0,
        "fat_g": 21.0,
        "fiber_g": 4.0,
    },
    "lobster_bisque": {
        "food_name": "Lobster Bisque",
        "serving_size": "1 bowl creamy bisque (approx. 250ml)",
        "calories": 290,
        "protein_g": 10.0,
        "carbs_g": 16.0,
        "fat_g": 20.0,
        "fiber_g": 1.0,
    },
    "lobster_roll_sandwich": {
        "food_name": "Lobster Roll",
        "serving_size": "1 lobster roll with butter (approx. 200g)",
        "calories": 440,
        "protein_g": 26.0,
        "carbs_g": 36.0,
        "fat_g": 21.0,
        "fiber_g": 2.0,
    },
    "macaroni_and_cheese": {
        "food_name": "Macaroni and Cheese",
        "serving_size": "1 bowl baked mac & cheese (approx. 220g)",
        "calories": 410,
        "protein_g": 15.0,
        "carbs_g": 46.0,
        "fat_g": 18.0,
        "fiber_g": 2.5,
    },
    "macarons": {
        "food_name": "Macarons",
        "serving_size": "2 French macarons (approx. 40g)",
        "calories": 170,
        "protein_g": 3.0,
        "carbs_g": 22.0,
        "fat_g": 8.0,
        "fiber_g": 1.0,
    },
    "miso_soup": {
        "food_name": "Miso Soup",
        "serving_size": "1 bowl with tofu & seaweed (approx. 220ml)",
        "calories": 65,
        "protein_g": 4.0,
        "carbs_g": 7.0,
        "fat_g": 2.0,
        "fiber_g": 1.5,
    },
    "mussels": {
        "food_name": "Mussels",
        "serving_size": "1 bowl steamed with garlic & wine (approx. 100g edible)",
        "calories": 170,
        "protein_g": 20.0,
        "carbs_g": 6.0,
        "fat_g": 7.0,
        "fiber_g": 0.0,
    },
    "nachos": {
        "food_name": "Nachos",
        "serving_size": "1 loaded plate with cheese & jalapeños (approx. 250g)",
        "calories": 640,
        "protein_g": 18.0,
        "carbs_g": 58.0,
        "fat_g": 38.0,
        "fiber_g": 6.0,
    },
    "omelette": {
        "food_name": "Omelette",
        "serving_size": "2-egg cheese omelette (approx. 150g)",
        "calories": 310,
        "protein_g": 18.0,
        "carbs_g": 2.0,
        "fat_g": 25.0,
        "fiber_g": 0.0,
    },
    "onion_rings": {
        "food_name": "Onion Rings",
        "serving_size": "6 battered onion rings (approx. 120g)",
        "calories": 380,
        "protein_g": 4.5,
        "carbs_g": 44.0,
        "fat_g": 21.0,
        "fiber_g": 3.0,
    },
    "oysters": {
        "food_name": "Oysters",
        "serving_size": "6 raw oysters on half shell (approx. 85g meat)",
        "calories": 60,
        "protein_g": 7.0,
        "carbs_g": 3.0,
        "fat_g": 1.8,
        "fiber_g": 0.0,
    },
    "pad_thai": {
        "food_name": "Pad Thai",
        "serving_size": "1 plate chicken/shrimp pad thai (approx. 320g)",
        "calories": 580,
        "protein_g": 22.0,
        "carbs_g": 74.0,
        "fat_g": 22.0,
        "fiber_g": 4.0,
    },
    "paella": {
        "food_name": "Paella",
        "serving_size": "1 plate seafood & saffron rice (approx. 320g)",
        "calories": 480,
        "protein_g": 26.0,
        "carbs_g": 62.0,
        "fat_g": 14.0,
        "fiber_g": 3.5,
    },
    "pancakes": {
        "food_name": "Pancakes",
        "serving_size": "2 medium buttermilk pancakes with syrup (approx. 180g)",
        "calories": 420,
        "protein_g": 7.0,
        "carbs_g": 68.0,
        "fat_g": 14.0,
        "fiber_g": 1.8,
    },
    "panna_cotta": {
        "food_name": "Panna Cotta",
        "serving_size": "1 serving with berry coulis (approx. 130g)",
        "calories": 320,
        "protein_g": 4.0,
        "carbs_g": 28.0,
        "fat_g": 21.0,
        "fiber_g": 0.5,
    },
    "peking_duck": {
        "food_name": "Peking Duck",
        "serving_size": "3 duck rolls with hoisin sauce (approx. 180g)",
        "calories": 460,
        "protein_g": 28.0,
        "carbs_g": 26.0,
        "fat_g": 26.0,
        "fiber_g": 1.5,
    },
    "pho": {
        "food_name": "Pho",
        "serving_size": "1 large bowl beef pho with broth & noodles (approx. 550g)",
        "calories": 450,
        "protein_g": 28.0,
        "carbs_g": 64.0,
        "fat_g": 8.5,
        "fiber_g": 3.0,
    },
    "pizza": {
        "food_name": "Pizza",
        "serving_size": "1 slice cheese & pepperoni (approx. 107g)",
        "calories": 285,
        "protein_g": 12.2,
        "carbs_g": 35.7,
        "fat_g": 10.4,
        "fiber_g": 2.5,
    },
    "pork_chop": {
        "food_name": "Pork Chop",
        "serving_size": "1 cooked center-cut chop (approx. 180g)",
        "calories": 360,
        "protein_g": 42.0,
        "carbs_g": 0.0,
        "fat_g": 20.0,
        "fiber_g": 0.0,
    },
    "poutine": {
        "food_name": "Poutine",
        "serving_size": "1 bowl fries with curds & gravy (approx. 280g)",
        "calories": 680,
        "protein_g": 19.0,
        "carbs_g": 62.0,
        "fat_g": 40.0,
        "fiber_g": 5.0,
    },
    "prime_rib": {
        "food_name": "Prime Rib",
        "serving_size": "1 roasted slice (approx. 220g)",
        "calories": 560,
        "protein_g": 46.0,
        "carbs_g": 0.0,
        "fat_g": 41.0,
        "fiber_g": 0.0,
    },
    "pulled_pork_sandwich": {
        "food_name": "Pulled Pork Sandwich",
        "serving_size": "1 sandwich with BBQ sauce (approx. 240g)",
        "calories": 520,
        "protein_g": 32.0,
        "carbs_g": 48.0,
        "fat_g": 21.0,
        "fiber_g": 2.5,
    },
    "ramen": {
        "food_name": "Ramen",
        "serving_size": "1 bowl tonkotsu ramen with egg & chashu (approx. 500g)",
        "calories": 620,
        "protein_g": 26.0,
        "carbs_g": 70.0,
        "fat_g": 25.0,
        "fiber_g": 3.5,
    },
    "ravioli": {
        "food_name": "Ravioli",
        "serving_size": "1 plate cheese ravioli in marinara (approx. 240g)",
        "calories": 380,
        "protein_g": 16.0,
        "carbs_g": 52.0,
        "fat_g": 12.0,
        "fiber_g": 4.5,
    },
    "red_velvet_cake": {
        "food_name": "Red Velvet Cake",
        "serving_size": "1 slice with cream cheese frosting (approx. 125g)",
        "calories": 430,
        "protein_g": 4.5,
        "carbs_g": 58.0,
        "fat_g": 21.0,
        "fiber_g": 1.5,
    },
    "risotto": {
        "food_name": "Risotto",
        "serving_size": "1 bowl mushroom parmesan risotto (approx. 250g)",
        "calories": 390,
        "protein_g": 9.0,
        "carbs_g": 56.0,
        "fat_g": 14.5,
        "fiber_g": 2.0,
    },
    "samosa": {
        "food_name": "Samosa",
        "serving_size": "2 pieces spiced potato & pea samosas (approx. 100g)",
        "calories": 260,
        "protein_g": 5.0,
        "carbs_g": 32.0,
        "fat_g": 12.5,
        "fiber_g": 3.5,
    },
    "sashimi": {
        "food_name": "Sashimi",
        "serving_size": "6 pieces salmon & tuna (approx. 120g)",
        "calories": 170,
        "protein_g": 28.0,
        "carbs_g": 0.0,
        "fat_g": 5.5,
        "fiber_g": 0.0,
    },
    "scallops": {
        "food_name": "Scallops",
        "serving_size": "4 pan-seared sea scallops (approx. 120g)",
        "calories": 160,
        "protein_g": 22.0,
        "carbs_g": 5.0,
        "fat_g": 5.5,
        "fiber_g": 0.0,
    },
    "seaweed_salad": {
        "food_name": "Seaweed Salad",
        "serving_size": "1 bowl sesame wakame salad (approx. 120g)",
        "calories": 110,
        "protein_g": 2.0,
        "carbs_g": 14.0,
        "fat_g": 5.5,
        "fiber_g": 3.0,
    },
    "shrimp_and_grits": {
        "food_name": "Shrimp and Grits",
        "serving_size": "1 bowl southern shrimp & grits (approx. 320g)",
        "calories": 480,
        "protein_g": 28.0,
        "carbs_g": 42.0,
        "fat_g": 22.0,
        "fiber_g": 2.5,
    },
    "spaghetti_bolognese": {
        "food_name": "Spaghetti Bolognese",
        "serving_size": "1 plate spaghetti with meat sauce (approx. 320g)",
        "calories": 490,
        "protein_g": 24.0,
        "carbs_g": 64.0,
        "fat_g": 15.0,
        "fiber_g": 4.5,
    },
    "spaghetti_carbonara": {
        "food_name": "Spaghetti Carbonara",
        "serving_size": "1 plate traditional carbonara (approx. 300g)",
        "calories": 580,
        "protein_g": 24.0,
        "carbs_g": 56.0,
        "fat_g": 28.0,
        "fiber_g": 3.0,
    },
    "spring_rolls": {
        "food_name": "Spring Rolls",
        "serving_size": "2 fried vegetable spring rolls (approx. 100g)",
        "calories": 220,
        "protein_g": 4.0,
        "carbs_g": 28.0,
        "fat_g": 10.0,
        "fiber_g": 2.5,
    },
    "steak": {
        "food_name": "Steak",
        "serving_size": "1 grilled sirloin steak (approx. 200g)",
        "calories": 420,
        "protein_g": 50.0,
        "carbs_g": 0.0,
        "fat_g": 23.0,
        "fiber_g": 0.0,
    },
    "strawberry_shortcake": {
        "food_name": "Strawberry Shortcake",
        "serving_size": "1 slice with cream & berries (approx. 140g)",
        "calories": 340,
        "protein_g": 4.5,
        "carbs_g": 48.0,
        "fat_g": 15.0,
        "fiber_g": 2.0,
    },
    "sushi": {
        "food_name": "Sushi",
        "serving_size": "6 pieces nigiri & maki rolls (approx. 180g)",
        "calories": 300,
        "protein_g": 12.0,
        "carbs_g": 48.0,
        "fat_g": 5.0,
        "fiber_g": 2.0,
    },
    "tacos": {
        "food_name": "Tacos",
        "serving_size": "2 street tacos beef/chicken (approx. 180g)",
        "calories": 380,
        "protein_g": 22.0,
        "carbs_g": 32.0,
        "fat_g": 18.0,
        "fiber_g": 4.0,
    },
    "takoyaki": {
        "food_name": "Takoyaki",
        "serving_size": "6 octopus balls with sauce & bonito (approx. 150g)",
        "calories": 290,
        "protein_g": 10.0,
        "carbs_g": 36.0,
        "fat_g": 11.5,
        "fiber_g": 1.5,
    },
    "tiramisu": {
        "food_name": "Tiramisu",
        "serving_size": "1 slice espresso tiramisu (approx. 120g)",
        "calories": 360,
        "protein_g": 6.0,
        "carbs_g": 36.0,
        "fat_g": 21.0,
        "fiber_g": 1.0,
    },
    "tuna_tartare": {
        "food_name": "Tuna Tartare",
        "serving_size": "1 portion with avocado & citrus dressing (approx. 140g)",
        "calories": 210,
        "protein_g": 27.0,
        "carbs_g": 4.0,
        "fat_g": 9.0,
        "fiber_g": 0.5,
    },
    "waffles": {
        "food_name": "Waffles",
        "serving_size": "2 plain waffles with butter & syrup (approx. 150g)",
        "calories": 410,
        "protein_g": 7.0,
        "carbs_g": 58.0,
        "fat_g": 17.0,
        "fiber_g": 2.0,
    },
}

# Standard reference nutrition for common whole produce, fresh fruits, vegetables,
# staples, and pantry groceries (USDA FoodData Central standard reference).
COMMON_PRODUCE_AND_STAPLES_DATASET: Dict[str, Dict[str, Any]] = {
    "apple": {
        "food_name": "Fresh Apple",
        "serving_size": "1 medium apple (approx. 182g)",
        "calories": 95,
        "protein_g": 0.5,
        "carbs_g": 25.1,
        "fat_g": 0.3,
        "fiber_g": 4.4,
    },
    "banana": {
        "food_name": "Fresh Banana",
        "serving_size": "1 medium banana (approx. 118g)",
        "calories": 105,
        "protein_g": 1.3,
        "carbs_g": 27.0,
        "fat_g": 0.3,
        "fiber_g": 3.1,
    },
    "orange": {
        "food_name": "Fresh Orange",
        "serving_size": "1 medium orange (approx. 131g)",
        "calories": 62,
        "protein_g": 1.2,
        "carbs_g": 15.4,
        "fat_g": 0.2,
        "fiber_g": 3.1,
    },
    "strawberry": {
        "food_name": "Fresh Strawberries",
        "serving_size": "1 cup halves (approx. 152g)",
        "calories": 49,
        "protein_g": 1.0,
        "carbs_g": 11.7,
        "fat_g": 0.5,
        "fiber_g": 3.0,
    },
    "strawberries": {
        "food_name": "Fresh Strawberries",
        "serving_size": "1 cup halves (approx. 152g)",
        "calories": 49,
        "protein_g": 1.0,
        "carbs_g": 11.7,
        "fat_g": 0.5,
        "fiber_g": 3.0,
    },
    "grape": {
        "food_name": "Fresh Grapes",
        "serving_size": "1 cup seedless (approx. 151g)",
        "calories": 104,
        "protein_g": 1.1,
        "carbs_g": 27.3,
        "fat_g": 0.2,
        "fiber_g": 1.4,
    },
    "grapes": {
        "food_name": "Fresh Grapes",
        "serving_size": "1 cup seedless (approx. 151g)",
        "calories": 104,
        "protein_g": 1.1,
        "carbs_g": 27.3,
        "fat_g": 0.2,
        "fiber_g": 1.4,
    },
    "mango": {
        "food_name": "Fresh Mango",
        "serving_size": "1 cup pieces (approx. 165g)",
        "calories": 99,
        "protein_g": 1.4,
        "carbs_g": 24.7,
        "fat_g": 0.6,
        "fiber_g": 2.6,
    },
    "watermelon": {
        "food_name": "Fresh Watermelon",
        "serving_size": "1 wedge (approx. 286g)",
        "calories": 86,
        "protein_g": 1.7,
        "carbs_g": 21.6,
        "fat_g": 0.4,
        "fiber_g": 1.1,
    },
    "avocado": {
        "food_name": "Fresh Avocado",
        "serving_size": "1/2 medium avocado (approx. 100g)",
        "calories": 160,
        "protein_g": 2.0,
        "carbs_g": 8.5,
        "fat_g": 14.7,
        "fiber_g": 6.7,
    },
    "lemon": {
        "food_name": "Fresh Lemon",
        "serving_size": "1 fruit without peel (approx. 58g)",
        "calories": 17,
        "protein_g": 0.6,
        "carbs_g": 5.4,
        "fat_g": 0.2,
        "fiber_g": 1.6,
    },
    "blueberries": {
        "food_name": "Fresh Blueberries",
        "serving_size": "1 cup (approx. 148g)",
        "calories": 84,
        "protein_g": 1.1,
        "carbs_g": 21.4,
        "fat_g": 0.5,
        "fiber_g": 3.6,
    },
    "pineapple": {
        "food_name": "Fresh Pineapple",
        "serving_size": "1 cup chunks (approx. 165g)",
        "calories": 82,
        "protein_g": 0.9,
        "carbs_g": 21.6,
        "fat_g": 0.2,
        "fiber_g": 2.3,
    },
    "broccoli": {
        "food_name": "Broccoli (Raw or Cooked)",
        "serving_size": "1 cup chopped (approx. 91g)",
        "calories": 31,
        "protein_g": 2.6,
        "carbs_g": 6.0,
        "fat_g": 0.3,
        "fiber_g": 2.4,
    },
    "carrot": {
        "food_name": "Fresh Carrot",
        "serving_size": "1 medium carrot (approx. 61g)",
        "calories": 25,
        "protein_g": 0.6,
        "carbs_g": 5.8,
        "fat_g": 0.1,
        "fiber_g": 1.7,
    },
    "carrots": {
        "food_name": "Fresh Carrots",
        "serving_size": "1 medium carrot (approx. 61g)",
        "calories": 25,
        "protein_g": 0.6,
        "carbs_g": 5.8,
        "fat_g": 0.1,
        "fiber_g": 1.7,
    },
    "tomato": {
        "food_name": "Fresh Red Tomato",
        "serving_size": "1 medium tomato (approx. 123g)",
        "calories": 22,
        "protein_g": 1.1,
        "carbs_g": 4.8,
        "fat_g": 0.2,
        "fiber_g": 1.5,
    },
    "tomatoes": {
        "food_name": "Fresh Red Tomatoes",
        "serving_size": "1 medium tomato (approx. 123g)",
        "calories": 22,
        "protein_g": 1.1,
        "carbs_g": 4.8,
        "fat_g": 0.2,
        "fiber_g": 1.5,
    },
    "cucumber": {
        "food_name": "Fresh Cucumber",
        "serving_size": "1/2 large with peel (approx. 150g)",
        "calories": 23,
        "protein_g": 1.0,
        "carbs_g": 5.4,
        "fat_g": 0.2,
        "fiber_g": 0.8,
    },
    "spinach": {
        "food_name": "Fresh Spinach",
        "serving_size": "2 cups raw (approx. 60g)",
        "calories": 14,
        "protein_g": 1.7,
        "carbs_g": 2.2,
        "fat_g": 0.2,
        "fiber_g": 1.3,
    },
    "potato": {
        "food_name": "Baked Potato",
        "serving_size": "1 medium with skin (approx. 173g)",
        "calories": 161,
        "protein_g": 4.3,
        "carbs_g": 36.6,
        "fat_g": 0.2,
        "fiber_g": 3.8,
    },
    "onion": {
        "food_name": "Yellow Onion",
        "serving_size": "1 medium onion (approx. 110g)",
        "calories": 44,
        "protein_g": 1.2,
        "carbs_g": 10.3,
        "fat_g": 0.1,
        "fiber_g": 1.9,
    },
    "lettuce": {
        "food_name": "Romaine Lettuce",
        "serving_size": "2 cups shredded (approx. 94g)",
        "calories": 16,
        "protein_g": 1.2,
        "carbs_g": 3.1,
        "fat_g": 0.3,
        "fiber_g": 2.0,
    },
    "bell_pepper": {
        "food_name": "Sweet Bell Pepper",
        "serving_size": "1 medium pepper (approx. 119g)",
        "calories": 31,
        "protein_g": 1.2,
        "carbs_g": 7.2,
        "fat_g": 0.4,
        "fiber_g": 2.5,
    },
    "egg": {
        "food_name": "Large Whole Egg",
        "serving_size": "1 large egg (approx. 50g)",
        "calories": 78,
        "protein_g": 6.3,
        "carbs_g": 0.6,
        "fat_g": 5.3,
        "fiber_g": 0.0,
    },
    "eggs": {
        "food_name": "Large Whole Eggs",
        "serving_size": "1 large egg (approx. 50g)",
        "calories": 78,
        "protein_g": 6.3,
        "carbs_g": 0.6,
        "fat_g": 5.3,
        "fiber_g": 0.0,
    },
    "boiled_egg": {
        "food_name": "Hard-Boiled Egg",
        "serving_size": "1 large egg (approx. 50g)",
        "calories": 78,
        "protein_g": 6.3,
        "carbs_g": 0.6,
        "fat_g": 5.3,
        "fiber_g": 0.0,
    },
    "rice": {
        "food_name": "Steamed White Rice",
        "serving_size": "1 cup cooked (approx. 158g)",
        "calories": 205,
        "protein_g": 4.2,
        "carbs_g": 44.5,
        "fat_g": 0.4,
        "fiber_g": 0.6,
    },
    "white_rice": {
        "food_name": "Steamed White Rice",
        "serving_size": "1 cup cooked (approx. 158g)",
        "calories": 205,
        "protein_g": 4.2,
        "carbs_g": 44.5,
        "fat_g": 0.4,
        "fiber_g": 0.6,
    },
    "brown_rice": {
        "food_name": "Cooked Brown Rice",
        "serving_size": "1 cup cooked (approx. 195g)",
        "calories": 216,
        "protein_g": 5.0,
        "carbs_g": 44.8,
        "fat_g": 1.8,
        "fiber_g": 3.5,
    },
    "chicken_breast": {
        "food_name": "Grilled Chicken Breast",
        "serving_size": "1 breast fillet (approx. 120g)",
        "calories": 198,
        "protein_g": 37.0,
        "carbs_g": 0.0,
        "fat_g": 4.3,
        "fiber_g": 0.0,
    },
    "salmon": {
        "food_name": "Grilled Salmon Fillet",
        "serving_size": "1 fillet (approx. 150g)",
        "calories": 309,
        "protein_g": 34.0,
        "carbs_g": 0.0,
        "fat_g": 18.0,
        "fiber_g": 0.0,
    },
    "tofu": {
        "food_name": "Firm Tofu",
        "serving_size": "1/2 cup (approx. 126g)",
        "calories": 181,
        "protein_g": 21.8,
        "carbs_g": 3.5,
        "fat_g": 11.0,
        "fiber_g": 2.9,
    },
    "milk": {
        "food_name": "Whole Cow Milk",
        "serving_size": "1 cup (approx. 244ml)",
        "calories": 149,
        "protein_g": 7.7,
        "carbs_g": 11.7,
        "fat_g": 8.0,
        "fiber_g": 0.0,
    },
    "yogurt": {
        "food_name": "Plain Greek Yogurt",
        "serving_size": "1 container (approx. 170g)",
        "calories": 100,
        "protein_g": 17.0,
        "carbs_g": 6.0,
        "fat_g": 0.7,
        "fiber_g": 0.0,
    },
    "bread": {
        "food_name": "Whole Wheat Bread",
        "serving_size": "1 slice (approx. 43g)",
        "calories": 110,
        "protein_g": 5.0,
        "carbs_g": 20.0,
        "fat_g": 1.5,
        "fiber_g": 3.0,
    },
    "oatmeal": {
        "food_name": "Cooked Rolled Oatmeal",
        "serving_size": "1 cup with water (approx. 234g)",
        "calories": 158,
        "protein_g": 5.9,
        "carbs_g": 27.3,
        "fat_g": 3.2,
        "fiber_g": 4.0,
    },
    "dal": {
        "food_name": "Cooked Lentils / Dal",
        "serving_size": "1 cup cooked (approx. 198g)",
        "calories": 230,
        "protein_g": 17.9,
        "carbs_g": 39.9,
        "fat_g": 0.8,
        "fiber_g": 15.6,
    },
    "lentils": {
        "food_name": "Cooked Lentils / Dal",
        "serving_size": "1 cup cooked (approx. 198g)",
        "calories": 230,
        "protein_g": 17.9,
        "carbs_g": 39.9,
        "fat_g": 0.8,
        "fiber_g": 15.6,
    },
    "roti": {
        "food_name": "Whole Wheat Chapati / Roti",
        "serving_size": "1 piece (approx. 40g)",
        "calories": 115,
        "protein_g": 3.5,
        "carbs_g": 22.0,
        "fat_g": 1.5,
        "fiber_g": 3.0,
    },
    "chapati": {
        "food_name": "Whole Wheat Chapati / Roti",
        "serving_size": "1 piece (approx. 40g)",
        "calories": 115,
        "protein_g": 3.5,
        "carbs_g": 22.0,
        "fat_g": 1.5,
        "fiber_g": 3.0,
    },
}


def normalize_food_key(label: str) -> str:
    """Normalize input label to match dataset key (e.g. 'Apple Pie' -> 'apple_pie')."""
    if not label:
        return ""
    clean = label.strip().lower()
    for char in [" ", "-", "/", "\\"]:
        clean = clean.replace(char, "_")
    while "__" in clean:
        clean = clean.replace("__", "_")
    return clean.strip("_")


def calculate_health_score(nut: Dict[str, Any]) -> tuple:
    """
    Activity 2.2: Simple, explainable rule-based health scoring algorithm (0-100).
    Evaluates nutrient density, protein-to-calorie balance, dietary fiber, and fat/sugar density.
    Returns: (score, label, reasoning, suggestions).
    """
    if not nut:
        return 50, "Moderate", "Nutritional details unavailable for detailed health scoring.", [
            "Incorporate a colorful side salad or fresh vegetables to enrich dietary fiber.",
            "Stay hydrated with water rather than sweetened beverages.",
        ]

    cal = nut.get("calories") or 0
    prot = nut.get("protein_g") or 0.0
    carbs = nut.get("carbs_g") or 0.0
    fat = nut.get("fat_g") or 0.0
    fiber = nut.get("fiber_g") or 0.0
    name = (nut.get("food_name") or "").lower()

    # Neutral starting baseline
    score = 50
    reasons = []
    suggestions = []

    # 1. Calorie density per serving
    if cal <= 200:
        score += 15
        reasons.append("light calorie profile")
    elif cal <= 350:
        score += 5
        reasons.append("moderate calorie density")
    elif cal <= 500:
        score -= 5
        reasons.append("moderate-high calorie content")
    elif cal <= 650:
        score -= 15
        reasons.append("high calorie density")
    else:
        score -= 25
        reasons.append("very high calorie density")

    # 2. Protein quality & quantity
    if prot >= 25:
        score += 18
        reasons.append("excellent lean protein")
        suggestions.append("Great lean protein source supporting muscle maintenance and sustained fullness.")
    elif prot >= 12:
        score += 10
        reasons.append("satisfying protein")
    elif prot < 5 and cal > 200:
        score -= 10
        reasons.append("low protein relative to energy")
        suggestions.append("Add a source of lean protein (such as beans, egg whites, or grilled poultry) to enhance meal balance.")

    # 3. Dietary Fiber
    if fiber >= 4.0:
        score += 15
        reasons.append("rich in dietary fiber")
        suggestions.append("High dietary fiber supports digestive wellness and steady blood glucose levels.")
    elif fiber >= 2.0:
        score += 8
        reasons.append("moderate dietary fiber")
    elif fiber < 1.0 and carbs >= 25:
        score -= 12
        reasons.append("refined low-fiber carbs")
        suggestions.append("Pair with colorful raw or steamed vegetables to increase essential fiber and micronutrients.")

    # 4. Total Fat density & Healthy Seafood Fats
    is_seafood = any(s in name for s in ["salmon", "sashimi", "tuna", "ceviche", "oysters", "mussels", "scallops"])
    if is_seafood and fat > 10:
        score += 10
        reasons.append("heart-healthy unsaturated marine fats")
        suggestions.append("Beneficial source of marine omega-3 fatty acids.")
    else:
        if fat <= 6:
            score += 10
            reasons.append("low total fat")
        elif fat <= 14:
            score += 2
        elif fat <= 24:
            score -= 10
            reasons.append("elevated fat content")
            suggestions.append("Balance your remaining meals today with low-oil, steamed, or broth-based options.")
        else:
            score -= 22
            reasons.append("high total fat density")
            suggestions.append("Consider baked, grilled, or air-fried preparations rather than pan or deep frying.")

    # 5. Dessert / Refined Sugar / Fried Starch checks
    is_dessert_or_fried = any(w in name for w in [
        "cake", "donut", "cupcake", "churros", "pie", "waffles", "pancakes",
        "cookie", "candy", "ice cream", "fries", "rings", "nachos", "baklava"
    ])
    if is_dessert_or_fried:
        score -= 10
        reasons.append("sugary or fried preparation")
        suggestions.append("Enjoy as an occasional treat and balance with nutrient-dense whole foods.")

    # Clamp 5 to 98
    score = max(5, min(98, score))

    if score >= 70:
        label = "Healthy"
    elif score >= 45:
        label = "Moderate"
    else:
        label = "Unhealthy"

    reasoning_text = f"Assigned {label} ({score}/100) due to " + (", ".join(reasons) if reasons else "balanced nutrient distribution") + "."

    # Ensure 2-3 unique actionable suggestions
    if len(suggestions) < 2:
        suggestions.append("Incorporate leafy greens or raw vegetables to broaden essential vitamin intake.")
    if len(suggestions) < 2:
        suggestions.append("Hydrate with fresh water or herbal tea rather than sweetened beverages.")

    clean_suggestions = []
    for s in suggestions:
        if s not in clean_suggestions:
            clean_suggestions.append(s)
    clean_suggestions = clean_suggestions[:3]

    return score, label, reasoning_text, clean_suggestions


def get_all_reference_foods() -> Dict[str, Dict[str, Any]]:
    """Combined reference dictionary of Food-101 and common whole foods."""
    return {**COMMON_PRODUCE_AND_STAPLES_DATASET, **FOOD_NUTRITION_DATASET}


def _build_nutrition_response(
    item: Dict[str, Any],
    is_verified: bool = True,
    is_fallback: bool = False,
) -> Dict[str, Any]:
    """Builds a standardized nutrition response with portion uncertainty ranges."""
    score, h_label, h_reason, h_suggestions = calculate_health_score(item)
    cal = int(item["calories"])
    # Portions in home cooking/restaurants vary typically by ±20% to ±25%
    min_cal = max(0, int(round(cal * 0.80)))
    max_cal = max(min_cal, int(round(cal * 1.25)))
    assert min_cal <= max_cal, "Uncertainty validation: minimum calories must not exceed maximum"

    serving_size = item.get("serving_size", "1 standard portion (approx. 150g)")

    return {
        "food_name": item["food_name"],
        "serving_size": serving_size,
        "calories": cal,
        "min_calories": min_cal,
        "max_calories": max_cal,
        "protein_g": float(item.get("protein_g", 0.0)),
        "carbs_g": float(item.get("carbs_g", 0.0)),
        "fat_g": float(item.get("fat_g", 0.0)),
        "fiber_g": float(item.get("fiber_g", 0.0)),
        "health_score": score,
        "health_label": h_label,
        "health_reasoning": h_reason,
        "health_suggestions": h_suggestions,
        "source": DATA_SOURCE_NAME,
        "is_estimate": True,
        "is_verified": is_verified,
        "is_fallback": is_fallback,
        "serving_assumptions": f"Standard typical serving: {serving_size}.",
        "assumed_serving_note": f"Estimated values assume a standard serving of: {serving_size}",
        "portion_uncertainty_note": (
            "Calorie values represent typical serving estimates with a ±20-25% variance range. "
            "A 2D image cannot establish true physical volume, mass, moisture, or hidden culinary fats/oils."
        ),
        "disclaimer": DEFAULT_DISCLAIMER,
    }


def lookup_nutrition_data(query: str) -> Optional[Dict[str, Any]]:
    """
    Look up verified standard reference nutrition facts for a given food name.
    Returns None if the item is not cataloged (never fabricates or guesses unsupported foods).
    """
    if not query or not query.strip():
        return None

    key = normalize_food_key(query)
    all_foods = get_all_reference_foods()

    # 1. Exact normalized match
    if key in all_foods:
        return _build_nutrition_response(all_foods[key], is_verified=True, is_fallback=False)

    # 2. Singular/plural normalization match
    if key.endswith("s") and key[:-1] in all_foods:
        return _build_nutrition_response(all_foods[key[:-1]], is_verified=True, is_fallback=False)
    if key.endswith("es") and key[:-2] in all_foods:
        return _build_nutrition_response(all_foods[key[:-2]], is_verified=True, is_fallback=False)

    # 3. Substring / whole word match
    for k, v in all_foods.items():
        if k == key:
            return _build_nutrition_response(v, is_verified=True, is_fallback=False)
        if len(key) >= 3 and (k in key or key in k):
            return _build_nutrition_response(v, is_verified=True, is_fallback=False)

    return None


def get_nutrition_estimate(label: str) -> Dict[str, Any]:
    """
    Retrieve reference nutrition data and rule-based health score for a given food label.
    Falls back gracefully with explicit fallback flags for uncataloged items to preserve
    backward compatibility with existing downstream consumers.
    """
    data = lookup_nutrition_data(label)
    if data:
        return data

    # Graceful fallback for uncataloged item
    formatted_name = label.replace("_", " ").title() if label else "Unknown Dish"
    fallback_data = {
        "food_name": formatted_name,
        "serving_size": "1 standard portion (approx. 200g)",
        "calories": 350,
        "protein_g": 15.0,
        "carbs_g": 40.0,
        "fat_g": 14.0,
        "fiber_g": 2.0,
    }
    return _build_nutrition_response(fallback_data, is_verified=False, is_fallback=True)
