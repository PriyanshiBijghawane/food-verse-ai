import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import User, UploadedAsset, FreshnessAssessment
from app.schemas.dtos import FreshnessAnalyzeResponse
from app.api.deps import get_current_user
from app.providers.factory import get_ai_provider
from app.services.upload_service import save_upload

router = APIRouter(prefix="/freshness", tags=["freshness"])

@router.post("/analyze", response_model=FreshnessAnalyzeResponse)
async def analyze_freshness(
    asset_id: Optional[str] = Form(None),
    food_type: str = Form("produce"),
    purchase_or_prep_date: Optional[str] = Form(None),
    storage_method: Optional[str] = Form("refrigerated"),
    packaging_condition: Optional[str] = Form("intact"),
    reported_odor_change: Optional[bool] = Form(False),
    reported_texture_change: Optional[bool] = Form(False),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image_bytes = b""
    active_asset_id = asset_id

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

    context = {
        "food_type": food_type,
        "purchase_or_prep_date": purchase_or_prep_date,
        "storage_method": storage_method,
        "packaging_condition": packaging_condition,
        "reported_odor_change": reported_odor_change,
        "reported_texture_change": reported_texture_change,
    }

    provider = get_ai_provider()
    res = await provider.assess_visible_freshness(image_bytes, context)

    category = res.get("spoilage_category", "insufficient_information")
    valid_categories = {
        "no_obvious_visible_spoilage",
        "possible_visible_spoilage",
        "visible_spoilage_observed",
        "insufficient_information",
    }
    if category not in valid_categories:
        category = "insufficient_information"

    limitations = res.get(
        "limitations",
        "Visual inspection cannot detect pathogens, tasteless toxins, or internal microbial contamination. "
        "Appearance alone does NOT guarantee food is safe to consume."
    )

    record = FreshnessAssessment(
        user_id=current_user.id,
        asset_id=active_asset_id,
        food_type=food_type,
        spoilage_category=category,
        visual_observations=res.get("visual_observations", []),
        storage_context=context,
        limitations=limitations,
        conservative_next_steps=res.get("conservative_next_steps", ["Discard if odor or slime is observed."]),
        safety_disclaimer=(
            "Visual inspection cannot establish microbiological food safety. "
            "Never taste food to determine if it has spoiled. When in doubt, discard."
        ),
        execution_mode=provider.execution_mode,
        provider=provider.provider_name,
        model_id=res.get("model_id"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return FreshnessAnalyzeResponse(
        id=record.id,
        food_type=record.food_type,
        spoilage_category=record.spoilage_category,
        category_label=record.spoilage_category.replace("_", " ").title(),
        visual_observations=record.visual_observations or [],
        storage_context=record.storage_context or {},
        limitations=record.limitations,
        conservative_next_steps=record.conservative_next_steps or [],
        execution_mode=record.execution_mode,
        provider=record.provider,
        model_id=record.model_id,
        created_at=record.created_at,
    )
