from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, EmailStr

# --- Auth Schemas ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: Optional[str] = "Food Verse User"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: str
    is_demo: bool = False

class UserOut(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool
    is_demo: bool
    created_at: float

# --- Profile Schemas ---
class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = "female"
    height_cm: Optional[float] = Field(None, ge=50.0, le=250.0)
    weight_kg: Optional[float] = Field(None, ge=20.0, le=300.0)
    activity_level: Optional[str] = "moderately_active"
    primary_goal: Optional[str] = "weight_loss"
    diet_type: Optional[str] = "balanced"
    allergies: Optional[List[str]] = Field(default_factory=list)
    food_restrictions: Optional[List[str]] = Field(default_factory=list)
    disliked_ingredients: Optional[List[str]] = Field(default_factory=list)
    cuisine_preferences: Optional[List[str]] = Field(default_factory=list)
    budget_preference: Optional[str] = "moderate"
    cooking_time_minutes: Optional[int] = 30
    household_size: Optional[int] = 1
    target_calories: Optional[float] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None

class ProfileOut(BaseModel):
    id: str
    user_id: str
    name: str
    email: Optional[str] = None
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    activity_level: str
    primary_goal: str
    diet_type: str
    allergies: List[str]
    food_restrictions: List[str]
    disliked_ingredients: List[str]
    cuisine_preferences: List[str]
    budget_preference: str
    cooking_time_minutes: int
    household_size: int
    target_calories: Optional[float] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None

# --- Upload Schemas ---
class AssetOut(BaseModel):
    id: str
    original_filename: str
    media_type: str
    mime_type: str
    size_bytes: int
    storage_path: Optional[str] = None
    created_at: float

# --- Food Analysis Schemas ---
class FoodAnalyzeRequest(BaseModel):
    asset_id: Optional[str] = None
    food_description: Optional[str] = None
    portion_grams: Optional[float] = 100.0
    portion_unit: Optional[str] = "grams"

class PortionRecalculateRequest(BaseModel):
    food_name: str
    portion_grams: float = Field(..., gt=0)
    portion_unit: str = "grams"

class DetectedFoodCandidate(BaseModel):
    label: str
    confidence: Optional[float] = None
    region: Optional[str] = None

class FoodAnalysisResponse(BaseModel):
    id: str
    food_name: str
    candidate_foods: List[DetectedFoodCandidate] = Field(default_factory=list)
    confidence: Optional[float] = None
    portion_grams: float
    portion_unit: str
    calories: Optional[float] = None  # None indicates unknown, not zero
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    nutritional_score: Optional[float] = None
    score_explanation: Optional[str] = None
    uncertainty_notes: Optional[str] = None
    detected_items: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: str
    execution_mode: str
    provider: str
    model_id: Optional[str] = None
    created_at: float
    safety_disclaimer: str = (
        "Nutrition values are estimates based on standard references and portion models. "
        "Appearance alone cannot determine nutritional content with clinical precision."
    )

# --- Freshness Schemas ---
class FreshnessAnalyzeRequest(BaseModel):
    asset_id: Optional[str] = None
    food_type: str = "general_produce"
    purchase_or_prep_date: Optional[str] = None
    storage_method: Optional[str] = "refrigerated"  # "refrigerated", "room_temperature", "frozen", "pantry"
    packaging_condition: Optional[str] = "intact"  # "intact", "opened", "damaged", "none"
    reported_odor_change: Optional[bool] = False
    reported_texture_change: Optional[bool] = False

class FreshnessAnalyzeResponse(BaseModel):
    id: str
    food_type: str
    spoilage_category: str  # "no_obvious_visible_spoilage" | "possible_visible_spoilage" | "visible_spoilage_observed" | "insufficient_information"
    category_label: str
    visual_observations: List[str]
    storage_context: Dict[str, Any]
    limitations: str
    conservative_next_steps: List[str]
    safety_disclaimer: str = (
        "Visual inspection cannot establish microbiological food safety or detect invisible pathogens, bacterial toxins, or internal contamination. "
        "An item with no visible spoilage is NOT guaranteed safe to eat. When in doubt, discard."
    )
    execution_mode: str
    provider: str
    model_id: Optional[str] = None
    created_at: float

# --- Hygiene Schemas ---
class HygieneAnalyzeRequest(BaseModel):
    asset_id: Optional[str] = None
    notes: Optional[str] = None

class HygieneFinding(BaseModel):
    area: str
    observation: str
    severity: str  # "info", "minor", "moderate", "critical"
    corrective_action: str
    timestamp_seconds: Optional[float] = None

class HygieneAnalyzeResponse(BaseModel):
    id: str
    media_type: str
    checklist_score: float
    score_formula: str
    findings: List[HygieneFinding]
    unobservable_items: List[str]
    non_certification_disclaimer: str = (
        "This observational checklist score reflects sampled visual conditions only and DOES NOT certify "
        "legal food safety compliance or health authority inspection standards."
    )
    execution_mode: str
    provider: str
    model_id: Optional[str] = None
    created_at: float

# --- Video Job Schemas ---
class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    status: str  # "queued", "processing", "succeeded", "failed"
    progress_percent: int
    execution_mode: str
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: float
    completed_at: Optional[float] = None

# --- Recipe Schemas ---
class RecipeGenerateRequest(BaseModel):
    ingredients: List[str] = Field(default_factory=list)
    from_food_analyses: Optional[List[str]] = None  # IDs of previous food analyses
    equipment: Optional[List[str]] = Field(default_factory=list)
    cooking_time_minutes: Optional[int] = 30
    cuisine_preference: Optional[str] = "Any"
    dietary_pattern: Optional[str] = "balanced"
    allergies: Optional[List[str]] = Field(default_factory=list)
    skill_level: Optional[str] = "intermediate"

class RecipeIngredientItem(BaseModel):
    name: str
    quantity: str
    unit: str
    optional: bool = False

class RecipeStepItem(BaseModel):
    step: int
    instruction: str
    timer_minutes: Optional[int] = None

class RecipeOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    ingredients: List[RecipeIngredientItem]
    servings: int
    prep_time_minutes: int
    cook_time_minutes: int
    instructions: List[RecipeStepItem]
    substitutions: List[Dict[str, str]]
    storage_guidance: Optional[str] = None
    nutrition_estimates: Dict[str, Any]
    allergen_warnings: List[str]
    is_saved: bool = False
    execution_mode: str
    provider: str
    created_at: float

# --- Meal Plan Schemas ---
class MealPlanGenerateRequest(BaseModel):
    plan_type: str = "7_day"  # "daily" | "7_day"
    target_calories: Optional[float] = None
    diet_type: Optional[str] = "balanced"
    allergies: Optional[List[str]] = Field(default_factory=list)
    disliked_ingredients: Optional[List[str]] = Field(default_factory=list)
    household_size: Optional[int] = 1

class MealReplaceRequest(BaseModel):
    day_number: int
    meal_type: str  # "breakfast", "lunch", "dinner", "snack"
    exclude_ingredients: Optional[List[str]] = Field(default_factory=list)

class MealItemOut(BaseModel):
    id: str
    day_number: int
    meal_type: str
    meal_name: str
    description: Optional[str] = None
    servings: int
    ingredients: List[str]
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None

class MealPlanOut(BaseModel):
    id: str
    title: str
    plan_type: str
    daily_target_calories: Optional[float] = None
    diet_type: str
    total_estimated_calories: Optional[float] = None
    total_protein_g: Optional[float] = None
    total_carbs_g: Optional[float] = None
    total_fat_g: Optional[float] = None
    allergen_notes: List[str]
    execution_mode: str
    created_at: float
    items: List[MealItemOut] = Field(default_factory=list)

class ShoppingListCategory(BaseModel):
    category: str
    items: List[str]

class ShoppingListOut(BaseModel):
    plan_id: str
    plan_title: str
    categories: List[ShoppingListCategory]
    total_distinct_items: int

# --- Chat & Audio Schemas ---
class ChatMessageIn(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    audio_transcribed: bool
    created_at: float

class AudioTranscribeResponse(BaseModel):
    transcript: str
    confidence: Optional[float] = None
    audio_duration_seconds: Optional[float] = None
    fallback_note: Optional[str] = None

# --- Capabilities & History Schemas ---
class CapabilitiesResponse(BaseModel):
    app_env: str
    ai_mode: str  # "demo" | "real"
    ai_provider: str
    ai_model: str
    has_api_key: bool
    supported_features: Dict[str, bool]
    disclaimers: Dict[str, str]

class HistoryItemOut(BaseModel):
    id: str
    type: str  # "food", "freshness", "hygiene", "recipe", "meal_plan"
    title: str
    summary: str
    execution_mode: str
    created_at: float
