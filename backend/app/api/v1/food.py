import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import User, UploadedAsset, FoodAnalysis
from app.schemas.dtos import FoodAnalysisResponse, PortionRecalculateRequest
from app.api.deps import get_current_user
from app.providers.factory import get_ai_provider
from app.services.upload_service import save_upload
from app.services.nutrition_service import get_portion_scaled_nutrition

router = APIRouter(prefix="/food", tags=["food"])

@router.post("/analyze", response_model=FoodAnalysisResponse)
async def analyze_food(
    asset_id: Optional[str] = Form(None),
    food_description: Optional[str] = Form(None),
    portion_grams: Optional[float] = Form(100.0),
    portion_unit: Optional[str] = Form("grams"),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image_bytes = b""
    active_asset_id = asset_id

    # If file was directly uploaded in this request
    if file and file.filename:
        saved_asset = await save_upload(file, current_user.id, db)
        active_asset_id = saved_asset.id
        with open(saved_asset.storage_path, "rb") as f:
            image_bytes = f.read()
    elif asset_id:
        asset = db.query(UploadedAsset).filter(UploadedAsset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Uploaded asset not found.")
        if os.path.exists(asset.storage_path):
            with open(asset.storage_path, "rb") as f:
                image_bytes = f.read()

    provider = get_ai_provider()
    analysis_dict = await provider.analyze_food_image(image_bytes, description=food_description)

    # Scale nutrition to user portion
    target_portion = portion_grams or analysis_dict.get("portion_grams", 100.0)
    scaled = get_portion_scaled_nutrition(
        analysis_dict.get("food_name", "Dish"),
        target_grams=target_portion,
        unit=portion_unit or "grams"
    )

    food_name = scaled["food_name"]
    calories = scaled["calories"]
    protein_g = scaled["protein_g"]
    carbs_g = scaled["carbs_g"]
    fat_g = scaled["fat_g"]
    fiber_g = scaled["fiber_g"]
    sodium_mg = scaled["sodium_mg"]
    score = scaled["nutritional_score"]
    score_expl = scaled["score_explanation"]

    record = FoodAnalysis(
        user_id=current_user.id,
        asset_id=active_asset_id,
        food_name=food_name,
        candidate_foods=analysis_dict.get("candidate_foods", []),
        confidence=analysis_dict.get("confidence"),
        portion_grams=target_portion,
        portion_unit=portion_unit or "grams",
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        fiber_g=fiber_g,
        sodium_mg=sodium_mg,
        nutritional_score=score,
        score_explanation=score_expl,
        detected_items=analysis_dict.get("detected_items", []),
        uncertainty_notes=analysis_dict.get("uncertainty_notes"),
        provenance=analysis_dict.get("provenance", "verified_reference"),
        execution_mode=provider.execution_mode,
        provider=provider.provider_name,
        model_id=analysis_dict.get("model_id"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return FoodAnalysisResponse(
        id=record.id,
        food_name=record.food_name,
        candidate_foods=record.candidate_foods or [],
        confidence=record.confidence,
        portion_grams=record.portion_grams,
        portion_unit=record.portion_unit,
        calories=record.calories,
        protein_g=record.protein_g,
        carbs_g=record.carbs_g,
        fat_g=record.fat_g,
        fiber_g=record.fiber_g,
        sodium_mg=record.sodium_mg,
        nutritional_score=record.nutritional_score,
        score_explanation=record.score_explanation,
        uncertainty_notes=record.uncertainty_notes,
        detected_items=record.detected_items or [],
        provenance=record.provenance,
        execution_mode=record.execution_mode,
        provider=record.provider,
        model_id=record.model_id,
        created_at=record.created_at,
    )

@router.post("/recalculate")
def recalculate_portion(req: PortionRecalculateRequest):
    """Dynamically scales verified nutritional values for user-edited portion size or grams."""
    result = get_portion_scaled_nutrition(req.food_name, target_grams=req.portion_grams, unit=req.portion_unit)
    return {"status": "success", "nutrition": result}
