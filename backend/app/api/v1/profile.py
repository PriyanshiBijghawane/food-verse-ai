from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import User, UserProfile
from app.schemas.dtos import ProfileUpdate, ProfileOut
from app.api.deps import get_current_user

router = APIRouter(tags=["profile"])

@router.get("/profile", response_model=ProfileOut)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return ProfileOut(
        id=profile.id,
        user_id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        age=profile.age,
        gender=profile.gender,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        activity_level=profile.activity_level,
        primary_goal=profile.primary_goal,
        diet_type=profile.diet_type,
        allergies=profile.allergies or [],
        food_restrictions=profile.food_restrictions or [],
        disliked_ingredients=profile.disliked_ingredients or [],
        cuisine_preferences=profile.cuisine_preferences or [],
        budget_preference=profile.budget_preference,
        cooking_time_minutes=profile.cooking_time_minutes,
        household_size=profile.household_size,
        target_calories=profile.target_calories,
        target_protein_g=profile.target_protein_g,
        target_carbs_g=profile.target_carbs_g,
        target_fat_g=profile.target_fat_g,
    )

@router.put("/profile", response_model=ProfileOut)
def update_profile(
    update_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if update_data.name:
        current_user.name = update_data.name
        db.add(current_user)

    for field, val in update_data.model_dump(exclude_unset=True).items():
        if field != "name" and hasattr(profile, field):
            setattr(profile, field, val)

    db.commit()
    db.refresh(profile)

    return ProfileOut(
        id=profile.id,
        user_id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        age=profile.age,
        gender=profile.gender,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        activity_level=profile.activity_level,
        primary_goal=profile.primary_goal,
        diet_type=profile.diet_type,
        allergies=profile.allergies or [],
        food_restrictions=profile.food_restrictions or [],
        disliked_ingredients=profile.disliked_ingredients or [],
        cuisine_preferences=profile.cuisine_preferences or [],
        budget_preference=profile.budget_preference,
        cooking_time_minutes=profile.cooking_time_minutes,
        household_size=profile.household_size,
        target_calories=profile.target_calories,
        target_protein_g=profile.target_protein_g,
        target_carbs_g=profile.target_carbs_g,
        target_fat_g=profile.target_fat_g,
    )
