"""
User Data, Profile, Settings & Notifications Router
Provides persistent storage and management for user profiles, app settings, and activity notifications.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("food_verse_ai.user_data")

router = APIRouter(prefix="/api/v1", tags=["user_data"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
NOTIFICATIONS_FILE = os.path.join(DATA_DIR, "notifications.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_json(file_path: str, default_val: Any) -> Any:
    _ensure_data_dir()
    if not os.path.exists(file_path):
        return default_val
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to read %s: %s. Using default.", file_path, exc)
        return default_val


def _save_json(file_path: str, data: Any):
    _ensure_data_dir()
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as exc:
        logger.error("Failed to write %s: %s", file_path, exc)
        raise HTTPException(status_code=500, detail=f"Failed to persist data: {exc}")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class UserProfile(BaseModel):
    name: str = Field(default="", max_length=100)
    email: Optional[str] = Field(default="", max_length=150)
    age: int = Field(default=28, ge=1, le=120)
    gender: str = Field(default="female")
    height_cm: float = Field(default=168.0, ge=50.0, le=250.0)
    weight_kg: float = Field(default=65.0, ge=20.0, le=300.0)
    activity_level: str = Field(default="moderately_active")
    primary_goal: str = Field(default="weight_loss")
    diet_type: str = Field(default="balanced")
    allergies: List[str] = Field(default_factory=list)
    food_restrictions: List[str] = Field(default_factory=list)
    cuisine_preferences: List[str] = Field(default_factory=lambda: ["Mediterranean", "Balanced"])

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        clean = v.strip().lower()
        allowed = {"male", "female", "other", "prefer_not_to_say"}
        if clean not in allowed:
            raise ValueError(f"Gender must be one of: {', '.join(sorted(allowed))}")
        return clean

    @field_validator("activity_level")
    @classmethod
    def validate_activity(cls, v: str) -> str:
        clean = v.strip().lower().replace(" ", "_")
        allowed = {"sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"}
        if clean not in allowed:
            raise ValueError(f"Activity level must be one of: {', '.join(sorted(allowed))}")
        return clean

    @field_validator("primary_goal")
    @classmethod
    def validate_goal(cls, v: str) -> str:
        clean = v.strip().lower().replace(" ", "_")
        allowed = {"weight_loss", "muscle_gain", "maintenance", "energy_boost", "heart_health"}
        if clean not in allowed:
            raise ValueError(f"Primary goal must be one of: {', '.join(sorted(allowed))}")
        return clean


class AppSettings(BaseModel):
    units: str = Field(default="metric", description="metric or imperial")
    default_diet: str = Field(default="balanced")
    default_cuisine: str = Field(default="Any")
    default_cooking_time: int = Field(default=30, ge=10, le=180)
    vision_confidence_threshold: float = Field(default=0.20, ge=0.05, le=0.95)
    in_app_notifications: bool = Field(default=True)

    @field_validator("units")
    @classmethod
    def validate_units(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in {"metric", "imperial"}:
            raise ValueError("Units must be 'metric' or 'imperial'")
        return clean


class NotificationItem(BaseModel):
    id: str = Field(..., description="Unique notification ID")
    title: str = Field(..., description="Notification headline")
    message: str = Field(..., description="Notification body")
    type: str = Field(default="info", description="info, success, warning, error")
    timestamp: float = Field(default_factory=time.time)
    read: bool = Field(default=False)
    module: Optional[str] = None


class MarkReadRequest(BaseModel):
    id: Optional[str] = None  # if None, mark all read


# ---------------------------------------------------------------------------
# Default States
# ---------------------------------------------------------------------------

DEFAULT_PROFILE = {
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "age": 28,
    "gender": "female",
    "height_cm": 168.0,
    "weight_kg": 65.0,
    "activity_level": "moderately_active",
    "primary_goal": "weight_loss",
    "diet_type": "balanced",
    "allergies": [],
    "food_restrictions": [],
    "cuisine_preferences": ["Mediterranean", "Balanced"]
}

DEFAULT_SETTINGS = {
    "units": "metric",
    "default_diet": "balanced",
    "default_cuisine": "Any",
    "default_cooking_time": 30,
    "vision_confidence_threshold": 0.20,
    "in_app_notifications": True
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/user/profile")
def get_user_profile():
    profile = _load_json(PROFILE_FILE, DEFAULT_PROFILE)
    return {"status": "success", "profile": profile}


@router.post("/user/profile")
def save_user_profile(profile: UserProfile):
    profile_dict = profile.model_dump()
    _save_json(PROFILE_FILE, profile_dict)
    return {"status": "success", "message": "Profile saved successfully", "profile": profile_dict}


@router.get("/user/settings")
def get_user_settings():
    settings = _load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
    return {"status": "success", "settings": settings}


@router.post("/user/settings")
def save_user_settings(settings: AppSettings):
    settings_dict = settings.model_dump()
    _save_json(SETTINGS_FILE, settings_dict)
    return {"status": "success", "message": "Settings saved successfully", "settings": settings_dict}


@router.get("/notifications")
def get_notifications():
    notifications = _load_json(NOTIFICATIONS_FILE, [])
    return {"status": "success", "notifications": notifications}


@router.post("/notifications")
def add_notification(item: NotificationItem):
    notifications = _load_json(NOTIFICATIONS_FILE, [])
    # Check if id already exists
    if any(n.get("id") == item.id for n in notifications):
        return {"status": "success", "message": "Notification already exists", "notification": item.model_dump()}
    # Prepend new notification
    notifications.insert(0, item.model_dump())
    # Keep up to 50 notifications
    notifications = notifications[:50]
    _save_json(NOTIFICATIONS_FILE, notifications)
    return {"status": "success", "message": "Notification added", "notification": item.model_dump()}


@router.post("/notifications/mark-read")
def mark_notification_read(req: MarkReadRequest):
    notifications = _load_json(NOTIFICATIONS_FILE, [])
    if req.id:
        for n in notifications:
            if n.get("id") == req.id:
                n["read"] = True
    else:
        for n in notifications:
            n["read"] = True
    _save_json(NOTIFICATIONS_FILE, notifications)
    return {"status": "success", "message": "Notifications marked as read", "notifications": notifications}


@router.post("/notifications/clear")
def clear_notifications():
    _save_json(NOTIFICATIONS_FILE, [])
    return {"status": "success", "message": "Notifications cleared", "notifications": []}
