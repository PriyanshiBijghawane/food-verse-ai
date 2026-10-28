import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_and_save_profile():
    # 1. Fetch current profile
    res = client.get("/api/v1/user/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "profile" in data

    # 2. Save updated profile
    payload = {
        "name": "Sarah Connor",
        "email": "sarah@example.com",
        "age": 32,
        "gender": "female",
        "height_cm": 172.0,
        "weight_kg": 68.0,
        "activity_level": "very_active",
        "primary_goal": "muscle_gain",
        "diet_type": "high_protein",
        "allergies": ["peanuts"],
        "food_restrictions": ["cilantro"],
        "cuisine_preferences": ["Mediterranean", "Asian"]
    }
    save_res = client.post("/api/v1/user/profile", json=payload)
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert save_data["status"] == "success"
    assert save_data["profile"]["name"] == "Sarah Connor"
    assert save_data["profile"]["age"] == 32

    # 3. Verify it persists
    check_res = client.get("/api/v1/user/profile")
    assert check_res.status_code == 200
    assert check_res.json()["profile"]["name"] == "Sarah Connor"


def test_profile_validation_errors():
    # Invalid age
    res = client.post("/api/v1/user/profile", json={"age": 150, "gender": "female", "height_cm": 170, "weight_kg": 65})
    assert res.status_code == 422

    # Invalid gender
    res = client.post("/api/v1/user/profile", json={"age": 25, "gender": "martian", "height_cm": 170, "weight_kg": 65})
    assert res.status_code == 422


def test_get_and_save_settings():
    # 1. Fetch current settings
    res = client.get("/api/v1/user/settings")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "settings" in data

    # 2. Save updated settings
    payload = {
        "units": "imperial",
        "default_diet": "vegan",
        "default_cuisine": "Italian",
        "default_cooking_time": 45,
        "vision_confidence_threshold": 0.35,
        "in_app_notifications": True
    }
    save_res = client.post("/api/v1/user/settings", json=payload)
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert save_data["status"] == "success"
    assert save_data["settings"]["units"] == "imperial"
    assert save_data["settings"]["default_cooking_time"] == 45

    # 3. Verify persistence
    check_res = client.get("/api/v1/user/settings")
    assert check_res.json()["settings"]["units"] == "imperial"


def test_notifications_flow():
    # Clear existing
    client.post("/api/v1/notifications/clear")

    # Add notification
    item = {
        "id": "notif-1",
        "title": "Meal Plan Synthesized",
        "message": "Daily 5-meal plan synthesized successfully.",
        "type": "success",
        "timestamp": 123456789.0,
        "read": False,
        "module": "meal-planner"
    }
    add_res = client.post("/api/v1/notifications", json=item)
    assert add_res.status_code == 200

    # Get notifications
    get_res = client.get("/api/v1/notifications")
    assert get_res.status_code == 200
    notifs = get_res.json()["notifications"]
    assert len(notifs) >= 1
    assert notifs[0]["id"] == "notif-1"
    assert notifs[0]["read"] is False

    # Mark as read
    mark_res = client.post("/api/v1/notifications/mark-read", json={"id": "notif-1"})
    assert mark_res.status_code == 200
    assert mark_res.json()["notifications"][0]["read"] is True

    # Clear notifications
    clear_res = client.post("/api/v1/notifications/clear")
    assert clear_res.status_code == 200
    assert len(clear_res.json()["notifications"]) == 0
