import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import (
    User,
    FoodAnalysis,
    FreshnessAssessment,
    HygieneAssessment,
    Recipe,
    MealPlan,
    UploadedAsset,
)
from app.schemas.dtos import HistoryItemOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/history", tags=["history"])

@router.get("", response_model=List[HistoryItemOut])
def get_user_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items = []

    # 1. Food Analyses
    food_records = db.query(FoodAnalysis).filter(FoodAnalysis.user_id == current_user.id).all()
    for f in food_records:
        items.append(
            HistoryItemOut(
                id=f.id,
                type="food",
                title=f.food_name,
                summary=f"Portion: {f.portion_grams}g | Calories: {f.calories or 'Unknown'} kcal | Score: {f.nutritional_score or 'N/A'}",
                execution_mode=f.execution_mode,
                created_at=f.created_at,
            )
        )

    # 2. Freshness Assessments
    fresh_records = db.query(FreshnessAssessment).filter(FreshnessAssessment.user_id == current_user.id).all()
    for fr in fresh_records:
        items.append(
            HistoryItemOut(
                id=fr.id,
                type="freshness",
                title=f"{fr.food_type.title()} Freshness Check",
                summary=f"Result: {fr.spoilage_category.replace('_', ' ').title()}",
                execution_mode=fr.execution_mode,
                created_at=fr.created_at,
            )
        )

    # 3. Hygiene Assessments
    hygiene_records = db.query(HygieneAssessment).filter(HygieneAssessment.user_id == current_user.id).all()
    for h in hygiene_records:
        items.append(
            HistoryItemOut(
                id=h.id,
                type="hygiene",
                title=f"Kitchen Inspection ({h.media_type.title()})",
                summary=f"Checklist Score: {h.checklist_score}/100 | Findings: {len(h.findings or [])}",
                execution_mode=h.execution_mode,
                created_at=h.created_at,
            )
        )

    # 4. Recipes
    recipe_records = db.query(Recipe).filter(Recipe.user_id == current_user.id).all()
    for r in recipe_records:
        items.append(
            HistoryItemOut(
                id=r.id,
                type="recipe",
                title=r.title,
                summary=f"Servings: {r.servings} | Prep: {r.prep_time_minutes}m | Cook: {r.cook_time_minutes}m",
                execution_mode=r.execution_mode,
                created_at=r.created_at,
            )
        )

    # 5. Meal Plans
    plan_records = db.query(MealPlan).filter(MealPlan.user_id == current_user.id).all()
    for p in plan_records:
        items.append(
            HistoryItemOut(
                id=p.id,
                type="meal_plan",
                title=p.title,
                summary=f"Type: {p.plan_type} | Target: {p.daily_target_calories} kcal/day",
                execution_mode=p.execution_mode,
                created_at=p.created_at,
            )
        )

    # Sort descending by timestamp
    items.sort(key=lambda x: x.created_at, reverse=True)
    return items

@router.delete("/{analysis_id}")
def delete_history_item(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    found = False

    # Check FoodAnalysis
    f = db.query(FoodAnalysis).filter(FoodAnalysis.id == analysis_id).first()
    if f:
        if f.user_id != current_user.id and not current_user.is_demo:
            raise HTTPException(status_code=403, detail="Unauthorized access to record.")
        if f.asset_id:
            asset = db.query(UploadedAsset).filter(UploadedAsset.id == f.asset_id).first()
            if asset and os.path.exists(asset.storage_path):
                try:
                    os.remove(asset.storage_path)
                except Exception:
                    pass
                db.delete(asset)
        db.delete(f)
        found = True

    # Check FreshnessAssessment
    fr = db.query(FreshnessAssessment).filter(FreshnessAssessment.id == analysis_id).first()
    if fr and not found:
        if fr.user_id != current_user.id and not current_user.is_demo:
            raise HTTPException(status_code=403, detail="Unauthorized access to record.")
        db.delete(fr)
        found = True

    # Check HygieneAssessment
    h = db.query(HygieneAssessment).filter(HygieneAssessment.id == analysis_id).first()
    if h and not found:
        if h.user_id != current_user.id and not current_user.is_demo:
            raise HTTPException(status_code=403, detail="Unauthorized access to record.")
        db.delete(h)
        found = True

    # Check Recipe
    r = db.query(Recipe).filter(Recipe.id == analysis_id).first()
    if r and not found:
        if r.user_id != current_user.id and not current_user.is_demo:
            raise HTTPException(status_code=403, detail="Unauthorized access to record.")
        db.delete(r)
        found = True

    # Check MealPlan
    p = db.query(MealPlan).filter(MealPlan.id == analysis_id).first()
    if p and not found:
        if p.user_id != current_user.id and not current_user.is_demo:
            raise HTTPException(status_code=403, detail="Unauthorized access to record.")
        db.delete(p)
        found = True

    if not found:
        raise HTTPException(status_code=404, detail="Item not found in history.")

    db.commit()
    return {"status": "success", "message": "History item and associated media deleted successfully."}
