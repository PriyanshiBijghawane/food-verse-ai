import os
import io
import time
import cv2
import logging
from typing import List, Tuple, Optional
from app.core.config import settings
from app.models.entities import AnalysisJob, UploadedAsset
from app.providers.factory import get_ai_provider

logger = logging.getLogger("food_verse_ai.job_worker")

def extract_video_frames(
    video_path: str, max_frames: int = 10, max_duration_sec: int = 60
) -> Tuple[List[Tuple[float, bytes]], float]:
    """
    Extracts bounded, timestamped JPEG frames from a video file using OpenCV.
    Guarantees bounded memory and processing overhead.
    """
    if not os.path.exists(video_path):
        raise ValueError(f"Video file not found at path: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open video file for decoding.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps if fps > 0 else 0.0

    if duration_sec > max_duration_sec:
        cap.release()
        raise ValueError(
            f"Video duration ({duration_sec:.1f}s) exceeds maximum allowed limit of {max_duration_sec}s."
        )

    if total_frames <= 0:
        cap.release()
        raise ValueError("Video contains no usable frame sequence.")

    # Calculate step interval to evenly sample max_frames across video
    actual_sample_count = min(max_frames, total_frames)
    step = max(1, total_frames // actual_sample_count)

    frames: List[Tuple[float, bytes]] = []
    frame_idx = 0

    while cap.isOpened() and len(frames) < actual_sample_count:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % step == 0:
            timestamp = round(frame_idx / fps, 2)
            # Resize frame to standard inspection resolution (max 800px width)
            h, w = frame.shape[:2]
            if w > 800:
                scale = 800.0 / w
                frame = cv2.resize(frame, (800, int(h * scale)))

            success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if success:
                frames.append((timestamp, buffer.tobytes()))

        frame_idx += 1

    cap.release()

    if not frames:
        raise ValueError("Failed to extract any decodable frames from video.")

    return frames, duration_sec

async def process_video_hygiene_job(job_id: str, db_factory):
    """
    Background worker task to extract frames and run hygiene audit.
    Updates the database record synchronously across lifecycle states.
    """
    db = db_factory()
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        db.close()
        return

    try:
        job.status = "processing"
        job.progress_percent = 20
        db.commit()

        asset_id = job.input_params.get("asset_id")
        asset = db.query(UploadedAsset).filter(UploadedAsset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Associated asset {asset_id} not found.")

        # Step 1: Extract frames (Progress 40%)
        frames, duration = extract_video_frames(
            asset.storage_path,
            max_frames=settings.MAX_VIDEO_FRAMES,
            max_duration_sec=settings.MAX_VIDEO_DURATION_SEC,
        )
        job.progress_percent = 50
        db.commit()

        # Step 2: Multimodal analysis (Progress 80%)
        provider = get_ai_provider()
        analysis_result = await provider.analyze_video_frames(frames)
        analysis_result["duration_seconds"] = duration
        analysis_result["total_frames_sampled"] = len(frames)

        # Step 3: Complete job (Progress 100%)
        job.status = "succeeded"
        job.progress_percent = 100
        job.result_data = analysis_result
        job.completed_at = time.time()
        db.commit()
    except Exception as exc:
        logger.exception("Error processing video hygiene job %s", job_id)
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = time.time()
        db.commit()
    finally:
        db.close()
