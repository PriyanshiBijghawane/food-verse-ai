import time
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(100), default="Food Verse User")
    is_active = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=False)
    created_at = Column(Float, default=time.time)
    updated_at = Column(Float, default=time.time, onupdate=time.time)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    assets = relationship("UploadedAsset", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("AnalysisJob", back_populates="user", cascade="all, delete-orphan")
    food_analyses = relationship("FoodAnalysis", back_populates="user", cascade="all, delete-orphan")
    freshness_assessments = relationship("FreshnessAssessment", back_populates="user", cascade="all, delete-orphan")
    hygiene_assessments = relationship("HygieneAssessment", back_populates="user", cascade="all, delete-orphan")
    recipes = relationship("Recipe", back_populates="user", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    age = Column(Integer, default=28)
    gender = Column(String(20), default="female")
    height_cm = Column(Float, default=168.0)
    weight_kg = Column(Float, default=65.0)
    activity_level = Column(String(50), default="moderately_active")
    primary_goal = Column(String(50), default="weight_loss")
    diet_type = Column(String(50), default="balanced")
    allergies = Column(JSON, default=list)
    food_restrictions = Column(JSON, default=list)
    disliked_ingredients = Column(JSON, default=list)
    cuisine_preferences = Column(JSON, default=lambda: ["Mediterranean", "Balanced"])
    budget_preference = Column(String(30), default="moderate")
    cooking_time_minutes = Column(Integer, default=30)
    household_size = Column(Integer, default=1)
    target_calories = Column(Float, nullable=True)
    target_protein_g = Column(Float, nullable=True)
    target_carbs_g = Column(Float, nullable=True)
    target_fat_g = Column(Float, nullable=True)
    updated_at = Column(Float, default=time.time, onupdate=time.time)

    user = relationship("User", back_populates="profile")


class UploadedAsset(Base):
    __tablename__ = "uploaded_assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    media_type = Column(String(50), nullable=False)  # "image" | "video" | "audio"
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(Float, default=time.time)

    user = relationship("User", back_populates="assets")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    job_type = Column(String(50), nullable=False)  # "video_hygiene", "food_batch", etc.
    status = Column(String(30), default="queued")  # "queued", "processing", "succeeded", "failed"
    progress_percent = Column(Integer, default=0)
    execution_mode = Column(String(20), default="demo")
    input_params = Column(JSON, default=dict)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(Float, default=time.time)
    completed_at = Column(Float, nullable=True)

    user = relationship("User", back_populates="jobs")


class FoodAnalysis(Base):
    __tablename__ = "food_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    asset_id = Column(String(36), ForeignKey("uploaded_assets.id"), nullable=True)
    food_name = Column(String(150), nullable=False)
    candidate_foods = Column(JSON, default=list)
    confidence = Column(Float, nullable=True)
    portion_grams = Column(Float, default=100.0)
    portion_unit = Column(String(50), default="grams")
    calories = Column(Float, nullable=True)
    protein_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)
    fiber_g = Column(Float, nullable=True)
    sodium_mg = Column(Float, nullable=True)
    nutritional_score = Column(Float, nullable=True)
    score_explanation = Column(Text, nullable=True)
    detected_items = Column(JSON, default=list)
    uncertainty_notes = Column(Text, nullable=True)
    provenance = Column(String(100), default="verified_reference")
    execution_mode = Column(String(20), default="demo")
    provider = Column(String(50), default="local")
    model_id = Column(String(100), nullable=True)
    created_at = Column(Float, default=time.time)

    user = relationship("User", back_populates="food_analyses")


class FreshnessAssessment(Base):
    __tablename__ = "freshness_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    asset_id = Column(String(36), ForeignKey("uploaded_assets.id"), nullable=True)
    food_type = Column(String(100), nullable=False)
    spoilage_category = Column(String(100), nullable=False)  # "no_obvious_visible_spoilage" | "possible_visible_spoilage" | "visible_spoilage_observed" | "insufficient_information"
    visual_observations = Column(JSON, default=list)
    storage_context = Column(JSON, default=dict)
    limitations = Column(Text, nullable=False)
    conservative_next_steps = Column(JSON, default=list)
    safety_disclaimer = Column(Text, nullable=False)
    execution_mode = Column(String(20), default="demo")
    provider = Column(String(50), default="local")
    model_id = Column(String(100), nullable=True)
    created_at = Column(Float, default=time.time)

    user = relationship("User", back_populates="freshness_assessments")


class HygieneAssessment(Base):
    __tablename__ = "hygiene_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    asset_id = Column(String(36), ForeignKey("uploaded_assets.id"), nullable=True)
    media_type = Column(String(20), default="image")  # "image" | "video"
    checklist_score = Column(Float, nullable=False)
    score_formula = Column(Text, nullable=False)
    findings = Column(JSON, default=list)  # area, observation, severity, corrective_action, timestamp
    unobservable_items = Column(JSON, default=list)
    non_certification_disclaimer = Column(Text, nullable=False)
    execution_mode = Column(String(20), default="demo")
    provider = Column(String(50), default="local")
    model_id = Column(String(100), nullable=True)
    created_at = Column(Float, default=time.time)

    user = relationship("User", back_populates="hygiene_assessments")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    ingredients = Column(JSON, default=list)  # list of {name, quantity, unit, optional}
    servings = Column(Integer, default=2)
    prep_time_minutes = Column(Integer, default=15)
    cook_time_minutes = Column(Integer, default=25)
    instructions = Column(JSON, default=list)  # list of {step, text, timer_minutes}
    substitutions = Column(JSON, default=list)
    storage_guidance = Column(Text, nullable=True)
    nutrition_estimates = Column(JSON, default=dict)
    allergen_warnings = Column(JSON, default=list)
    is_saved = Column(Boolean, default=False)
    execution_mode = Column(String(20), default="demo")
    provider = Column(String(50), default="local")
    created_at = Column(Float, default=time.time)

    user = relationship("User", back_populates="recipes")


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), default="Personalized Meal Plan")
    plan_type = Column(String(20), default="7_day")  # "daily" | "7_day"
    daily_target_calories = Column(Float, nullable=True)
    diet_type = Column(String(50), default="balanced")
    total_estimated_calories = Column(Float, nullable=True)
    total_protein_g = Column(Float, nullable=True)
    total_carbs_g = Column(Float, nullable=True)
    total_fat_g = Column(Float, nullable=True)
    allergen_notes = Column(JSON, default=list)
    execution_mode = Column(String(20), default="demo")
    created_at = Column(Float, default=time.time)

    user = relationship("User", back_populates="meal_plans")
    items = relationship("MealPlanItem", back_populates="meal_plan", cascade="all, delete-orphan")


class MealPlanItem(Base):
    __tablename__ = "meal_plan_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    meal_plan_id = Column(String(36), ForeignKey("meal_plans.id"), nullable=False)
    day_number = Column(Integer, default=1)  # 1 to 7
    meal_type = Column(String(30), nullable=False)  # "breakfast", "lunch", "dinner", "snack"
    meal_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    servings = Column(Integer, default=1)
    ingredients = Column(JSON, default=list)
    calories = Column(Float, nullable=True)
    protein_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)

    meal_plan = relationship("MealPlan", back_populates="items")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), default="Cooking Assistant Chat")
    created_at = Column(Float, default=time.time)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" | "assistant" | "system"
    content = Column(Text, nullable=False)
    audio_transcribed = Column(Boolean, default=False)
    created_at = Column(Float, default=time.time)

    session = relationship("ChatSession", back_populates="messages")
