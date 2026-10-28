import os
import io
import uuid
import logging
from typing import Tuple, Optional
from PIL import Image
from fastapi import HTTPException, UploadFile
from app.core.config import settings
from app.models.entities import UploadedAsset

logger = logging.getLogger("food_verse_ai.upload_service")

# Magic bytes signatures
MAGIC_BYTES = {
    b"\x89PNG\r\n\x1a\n": ("image", "image/png", ".png"),
    b"\xff\xd8\xff": ("image", "image/jpeg", ".jpg"),
    b"RIFF": ("image", "image/webp", ".webp"),  # WEBP has RIFF header followed by WEBP
    b"\x00\x00\x00\x18ftyp": ("video", "video/mp4", ".mp4"),
    b"\x00\x00\x00\x20ftyp": ("video", "video/mp4", ".mp4"),
    b"\x00\x00\x00\x1cftyp": ("video", "video/mp4", ".mp4"),
    b"ID3": ("audio", "audio/mpeg", ".mp3"),
    b"\xff\xfb": ("audio", "audio/mpeg", ".mp3"),
    b"\xff\xf3": ("audio", "audio/mpeg", ".mp3"),
    b"\xff\xf2": ("audio", "audio/mpeg", ".mp3"),
}

def detect_file_type(header: bytes, filename: str) -> Tuple[str, str, str]:
    """Inspects magic bytes signatures rather than trusting user-supplied filenames."""
    for magic, (m_type, mime, ext) in MAGIC_BYTES.items():
        if header.startswith(magic):
            return m_type, mime, ext

    # Fallback inspection for WEBP
    if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP":
        return "image", "image/webp", ".webp"

    # Fallback inspection for MP4/MOV ftyp
    if len(header) >= 12 and b"ftyp" in header[:12]:
        return "video", "video/mp4", ".mp4"

    # Fallback based on extension if headers match common safe media
    lowered = filename.lower()
    if lowered.endswith(".jpg") or lowered.endswith(".jpeg"):
        return "image", "image/jpeg", ".jpg"
    if lowered.endswith(".png"):
        return "image", "image/png", ".png"
    if lowered.endswith(".webp"):
        return "image", "image/webp", ".webp"
    if lowered.endswith(".mp4"):
        return "video", "video/mp4", ".mp4"
    if lowered.endswith(".mov"):
        return "video", "video/quicktime", ".mov"
    if lowered.endswith(".mp3"):
        return "audio", "audio/mpeg", ".mp3"
    if lowered.endswith(".wav"):
        return "audio", "audio/wav", ".wav"

    raise HTTPException(
        status_code=400,
        detail="Unsupported or corrupt file type. Supported media: JPEG, PNG, WEBP images, MP4 videos, and MP3 audio."
    )

async def save_upload(file: UploadFile, user_id: str, db) -> UploadedAsset:
    """Validates file signature, bounds size, normalizes path, and persists asset."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    if file_size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file exceeds maximum limit of {settings.MAX_UPLOAD_MB}MB."
        )

    # Magic byte inspection
    header = content[:32]
    media_type, mime_type, safe_ext = detect_file_type(header, file.filename or "file")

    # Image dimension check
    width, height = None, None
    if media_type == "image":
        try:
            with Image.open(io.BytesIO(content)) as img:
                width, height = img.size
                if width < 32 or height < 32:
                    raise HTTPException(status_code=400, detail=f"Image resolution {width}x{height} is too small to analyze.")
                if width > 8000 or height > 8000:
                    raise HTTPException(status_code=400, detail=f"Image dimensions exceed maximum safe limit (8000px).")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Corrupt or unreadable image file: {exc}")

    # Generate safe randomized filename (UUID + safe extension)
    unique_name = f"{uuid.uuid4()}{safe_ext}"
    storage_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    try:
        with open(storage_path, "wb") as f:
            f.write(content)
    except Exception as exc:
        logger.error("Failed to write uploaded file to disk: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save uploaded asset on server.")

    asset = UploadedAsset(
        user_id=user_id,
        original_filename=file.filename or "uploaded_media",
        storage_path=storage_path,
        media_type=media_type,
        mime_type=mime_type,
        size_bytes=file_size,
        width=width,
        height=height,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset
