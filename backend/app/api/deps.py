from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.entities import User, UserProfile

DEMO_USER_EMAIL = "demo@foodverse.ai"

def get_or_create_demo_user(db: Session) -> User:
    """Ensures a default demo user exists for out-of-the-box evaluation without mandatory login."""
    user = db.query(User).filter(User.email == DEMO_USER_EMAIL).first()
    if not user:
        user = User(
            email=DEMO_USER_EMAIL,
            hashed_password="demo_hashed_password_placeholder",
            name="Demo Food Verse User",
            is_active=True,
            is_demo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create corresponding profile
        profile = UserProfile(
            user_id=user.id,
            age=28,
            gender="female",
            height_cm=168.0,
            weight_kg=65.0,
            activity_level="moderately_active",
            primary_goal="weight_loss",
            diet_type="balanced",
            allergies=[],
            food_restrictions=[],
            disliked_ingredients=[],
            cuisine_preferences=["Mediterranean", "Balanced"],
        )
        db.add(profile)
        db.commit()

    return user

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates Bearer token if provided. If absent, transparently provides the safe demo user
    so all flows remain immediately interactive without blocking the user.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            user_id = payload["sub"]
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_active:
                return user

    # Default to demo user for seamless local evaluation
    return get_or_create_demo_user(db)
