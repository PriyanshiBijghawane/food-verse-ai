from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import User, UploadedAsset
from app.schemas.dtos import AssetOut
from app.api.deps import get_current_user
from app.services.upload_service import save_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])

@router.post("", response_model=AssetOut)
async def upload_asset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    asset = await save_upload(file, current_user.id, db)
    return AssetOut(
        id=asset.id,
        original_filename=asset.original_filename,
        media_type=asset.media_type,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
        storage_path=asset.storage_path,
        created_at=asset.created_at,
    )
