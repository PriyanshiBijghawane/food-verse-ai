import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.models.entities import User, UploadedAsset, HygieneAssessment, AnalysisJob
from app.schemas.dtos import HygieneAnalyzeResponse, JobStatusResponse
from app.api.deps import get_current_user
from app.providers.factory import get_ai_provider
from app.services.upload_service import save_upload
from app.services.job_worker import process_video_hygiene_job

router = APIRouter(prefix="/hygiene", tags=["hygiene"])

@router.post("/analyze")
async def analyze_hygiene(
    background_tasks: BackgroundTasks,
    asset_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    media_type = "image"
    active_asset_id = asset_id
    image_bytes = b""

    if file and file.filename:
        saved_asset = await save_upload(file, current_user.id, db)
        active_asset_id = saved_asset.id
        media_type = saved_asset.media_type
    elif asset_id:
        asset = db.query(UploadedAsset).filter(UploadedAsset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Uploaded asset not found.")
        media_type = asset.media_type

    # If media is video: launch asynchronous background analysis job
    if media_type == "video":
        provider = get_ai_provider()
        job = AnalysisJob(
            user_id=current_user.id,
            job_type="video_hygiene",
            status="queued",
            progress_percent=5,
            execution_mode=provider.execution_mode,
            input_params={"asset_id": active_asset_id, "notes": notes},
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Dispatch async worker
        background_tasks.add_task(process_video_hygiene_job, job.id, SessionLocal)

        return {
            "status": "queued",
            "message": "Video hygiene analysis job initiated. Bounded frames will be sampled for evaluation.",
            "job": {
                "job_id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "progress_percent": job.progress_percent,
                "execution_mode": job.execution_mode,
                "created_at": job.created_at,
            }
        }

    # For image media: perform immediate synchronous audit
    asset = db.query(UploadedAsset).filter(UploadedAsset.id == active_asset_id).first()
    if asset and os.path.exists(asset.storage_path):
        with open(asset.storage_path, "rb") as f:
            image_bytes = f.read()

    provider = get_ai_provider()
    res = await provider.analyze_kitchen_image(image_bytes, notes)

    checklist_score = float(res.get("checklist_score", 85.0))
    score_formula = res.get(
        "score_formula",
        "Observational Checklist Score: Base 100 - (15 pts * Critical) - (10 pts * Moderate) - (5 pts * Minor)."
    )
    findings = res.get("findings", [])
    unobservable = res.get("unobservable_items", [
        "Internal sanitizer chemical PPM (requires chemical strip test)",
        "Internal food probe temperatures",
    ])

    record = HygieneAssessment(
        user_id=current_user.id,
        asset_id=active_asset_id,
        media_type="image",
        checklist_score=checklist_score,
        score_formula=score_formula,
        findings=findings,
        unobservable_items=unobservable,
        non_certification_disclaimer=(
            "Observational checklist score is derived from visible conditions in the image. "
            "It DOES NOT certify compliance with local public health regulations, HACCP plans, or legal food safety codes."
        ),
        execution_mode=provider.execution_mode,
        provider=provider.provider_name,
        model_id=res.get("model_id"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return HygieneAnalyzeResponse(
        id=record.id,
        media_type=record.media_type,
        checklist_score=record.checklist_score,
        score_formula=record.score_formula,
        findings=record.findings or [],
        unobservable_items=record.unobservable_items or [],
        execution_mode=record.execution_mode,
        provider=record.provider,
        model_id=record.model_id,
        created_at=record.created_at,
    )
