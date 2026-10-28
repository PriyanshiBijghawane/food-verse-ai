from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import User, AnalysisJob
from app.schemas.dtos import JobStatusResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Ownership check: verify user owns this job
    if job.user_id != current_user.id and not current_user.is_demo:
        raise HTTPException(status_code=403, detail="Unauthorized access to job record.")

    return JobStatusResponse(
        job_id=job.id,
        job_type=job.job_type,
        status=job.status,
        progress_percent=job.progress_percent,
        execution_mode=job.execution_mode,
        result_data=job.result_data,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
