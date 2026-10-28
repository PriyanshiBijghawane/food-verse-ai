import io
import logging
from contextlib import asynccontextmanager

import torch
import torch.nn.functional as F
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError
from transformers import AutoImageProcessor, AutoModelForImageClassification

from nutrition_data import get_nutrition_estimate, lookup_nutrition_data
from routers.freshness_detector import router as freshness_router
from routers.hygiene_monitor import router as hygiene_router
from routers.kitchen_assistant import router as kitchen_router
from routers.meal_planner import router as meal_planner_router
from routers.user_data import router as user_data_router
from app.core.config import settings
from app.db.session import init_db
from app.api.v1 import api_v1_router

logger = logging.getLogger("food_verse_ai")

# ---------------------------------------------------------------------------
# Model globals – populated once during application startup via the lifespan
# ---------------------------------------------------------------------------
MODEL_ID = "nateraw/food"  # ViT-base fine-tuned on Food-101 (~89 % accuracy)

_model = None
_processor = None
_model_ready = False
_model_error: str | None = None
_device: str = "cuda" if torch.cuda.is_available() else "cpu"


def preprocess_image(image: Image.Image) -> tuple[Image.Image, dict]:
    """
    Activity 2.1: Preprocessing pipeline.
    - Preserves natural food color saturation and hue (avoids artificial autocontrast)
    - Validates minimum dimensions and rescales extreme resolutions using LANCZOS
    - Records illumination and contrast diagnostics
    """
    meta = {
        "exif_transposed": True,
        "contrast_enhanced": False,
        "lighting_notes": "Natural exposure & dynamic range preserved",
    }

    w, h = image.size
    meta["original_resolution"] = f"{w}x{h}"

    # Minimum dimension validation (Activity 2.1 input validation)
    if w < 64 or h < 64:
        raise ValueError(f"Image resolution ({w}x{h}) is too small. Minimum supported resolution is 64x64.")

    # Rescale excessively large photos to max 1600px while preserving aspect ratio
    max_dim = 1600
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        new_w, new_h = max(64, int(w * scale)), max(64, int(h * scale))
        image = image.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
        meta["processed_resolution"] = f"{new_w}x{new_h}"
    else:
        meta["processed_resolution"] = f"{w}x{h}"

    # Lighting variations diagnostics without distorting natural food colors
    grayscale = image.convert("L")
    stat = ImageStat.Stat(grayscale)
    mean_lum = stat.mean[0]
    std_lum = stat.stddev[0]
    meta["mean_luminance"] = round(mean_lum, 1)
    meta["contrast_stddev"] = round(std_lum, 1)

    if mean_lum < 40.0:
        meta["lighting_notes"] = "Low ambient lighting detected (natural colors preserved without artificial contrast distortion)"
    elif mean_lum > 220.0:
        meta["lighting_notes"] = "High brightness / overexposed lighting detected"

    return image, meta


def analyze_complex_arrangement(
    image: Image.Image,
    model,
    processor,
    primary_label: str,
    device: str = "cpu",
    min_confidence: float = 0.45,
) -> tuple[list[dict], bool]:
    """
    Evaluates potential distinct multi-dish regions in composite platters.
    
    IMPORTANT ARCHITECTURAL LIMITATION:
    Spatial grid windowing on a closed-set classifier is an exploratory heuristic, NOT a
    bounding-box object detector (e.g. YOLO, Faster R-CNN, or Mask R-CNN). Arbitrary slicing
    across dish borders can create misleading false positives.
    To avoid false positives:
    - Requires candidate confidence >= 0.45 (well above random uniform probability 1/101 ~ 0.01).
    - Only considers sub-regions that distinctly differ from the global primary dish.
    """
    w, h = image.size

    # Skip cropping for small images or single-item plates
    if w < 256 or h < 256:
        return [], False

    # Candidate quadrant regions with margin padding to reduce border cuts
    zones = [
        ("Top-Left Zone", (0.05, 0.05, 0.55, 0.55)),
        ("Top-Right Zone", (0.45, 0.05, 0.95, 0.55)),
        ("Bottom-Left Zone", (0.05, 0.45, 0.55, 0.95)),
        ("Bottom-Right Zone", (0.45, 0.45, 0.95, 0.95)),
    ]

    crops = []
    zone_boxes = []
    for name, (rx1, ry1, rx2, ry2) in zones:
        box = (int(rx1 * w), int(ry1 * h), int(rx2 * w), int(ry2 * h))
        crops.append(image.crop(box))
        zone_boxes.append((name, {"x1": rx1, "y1": ry1, "x2": rx2, "y2": ry2}))

    # Batched inference over spatial crops
    inputs = processor(images=crops, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=-1)

    top_probs, top_indices = torch.topk(probs, k=1, dim=-1)

    # Collect detections that pass conservative threshold and differ from primary
    candidates = []
    for i, (name, box_coords) in enumerate(zone_boxes):
        conf = top_probs[i][0].item()
        idx = top_indices[i][0].item()
        raw = model.config.id2label[idx]
        display = raw.replace("_", " ").title()

        if conf >= min_confidence and raw != primary_label:
            candidates.append({
                "raw_label": raw,
                "label": display,
                "confidence": round(conf, 4),
                "region": name,
                "box": box_coords,
            })

    # Deduplication across overlapping regions
    unique_dishes = {}
    for item in candidates:
        lbl = item["raw_label"]
        if lbl not in unique_dishes or item["confidence"] > unique_dishes[lbl]["confidence"]:
            unique_dishes[lbl] = item

    distinct_items = list(unique_dishes.values())
    distinct_items.sort(key=lambda x: x["confidence"], reverse=True)

    is_multi_item = len(distinct_items) >= 1

    detected_items = []
    for idx, item in enumerate(distinct_items, start=1):
        nut = get_nutrition_estimate(item["raw_label"])
        detected_items.append({
            "item_id": idx,
            "label": item["label"],
            "confidence": item["confidence"],
            "region": item["region"],
            "box": item["box"],
            "nutrition": nut,
        })

    return detected_items, is_multi_item


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load the food-recognition model at startup, release on shutdown.
    Ensures application startup succeeds even if model download or initialization fails.
    """
    global _model, _processor, _model_ready, _model_error, _device

    _device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        logger.info("Initializing food-recognition model '%s' on %s …", MODEL_ID, _device)
        _processor = AutoImageProcessor.from_pretrained(MODEL_ID)
        _model = AutoModelForImageClassification.from_pretrained(MODEL_ID)
        _model.to(_device)
        _model.eval()
        _model_ready = True
        _model_error = None
        logger.info("Model loaded successfully on %s.", _device)
    except Exception as exc:
        _model_error = f"{type(exc).__name__}: {str(exc)}"
        _model = None
        _processor = None
        _model_ready = False
        logger.error("Failed to load model during startup: %s", _model_error)

    # Initialize database tables
    try:
        init_db()
        logger.info("SQLAlchemy database tables initialized successfully.")
    except Exception as exc:
        logger.warning("Database initialization warning: %s", exc)

    yield  # application runs

    # cleanup
    _model = None
    _processor = None
    _model_ready = False


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(title="Food Verse AI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Version 1 API routers (all new epics, auth, jobs, history, capabilities)
app.include_router(api_v1_router)

# Legacy routers (preserved for backward compatibility with existing tests)
app.include_router(freshness_router)
app.include_router(hygiene_router)
app.include_router(kitchen_router)
app.include_router(meal_planner_router)
app.include_router(user_data_router)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "ok",
        "application_status": "healthy",
        "model_ready": _model_ready,
        "model_id": MODEL_ID,
        "device": _device,
        "model_error": _model_error,
        "ai_mode": settings.AI_MODE,
        "ai_provider": settings.AI_PROVIDER,
    }


@app.get("/api/v1/food/nutrition")
def get_food_nutrition(food: str | None = None, query: str | None = None):
    """
    Retrieve estimated reference nutrition facts for a given food label or search query.
    Supports:
      - GET /api/v1/food/nutrition?query=apple
      - GET /api/v1/food/nutrition?food=pizza (backward compatible)
    Returns verified standard reference facts with portion uncertainty ranges.
    Returns HTTP 404 for uncataloged items when queried directly.
    """
    term = query if query is not None else food
    if not term or not term.strip():
        raise HTTPException(
            status_code=400,
            detail="Please specify a food item using the 'query' or 'food' parameter.",
        )

    clean_term = term.strip()
    verified_data = lookup_nutrition_data(clean_term)
    if verified_data:
        return verified_data

    # If queried via legacy 'food' param, provide fallback for backward compatibility
    if food and query is None:
        return get_nutrition_estimate(clean_term)

    # For text-based 'query', return a clear 404 instead of fabricating values
    raise HTTPException(
        status_code=404,
        detail=f"Nutrition facts for '{clean_term}' were not found in the verified food reference database. To avoid inaccurate dietary guidance, speculative estimates are not fabricated.",
    )


@app.post("/api/v1/food/recognize")
async def recognize_food(file: UploadFile = File(...)):
    # --- guard: model must be loaded ----------------------------------------
    if not _model_ready:
        raise HTTPException(
            status_code=503,
            detail=f"Model is not available. {_model_error or 'Still loading or unavailable'}",
        )

    # --- guard: content-type must be image -----------------------------------
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a valid image file (PNG, JPG, WEBP).",
        )

    # --- read & decode image with EXIF-first preprocessing --------------------
    try:
        max_upload_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        raw_bytes = await file.read(max_upload_bytes + 1)
        if len(raw_bytes) > max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Image exceeds the maximum upload size of {settings.MAX_UPLOAD_MB} MB.",
            )
        raw_img = Image.open(io.BytesIO(raw_bytes))
        # Apply EXIF transposition BEFORE converting to RGB
        try:
            transposed_img = ImageOps.exif_transpose(raw_img)
        except Exception:
            transposed_img = raw_img

        rgb_img = transposed_img.convert("RGB")
        image, prep_meta = preprocess_image(rgb_img)
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file could not be decoded as an image. Please upload a valid image file.",
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail=str(ve),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading image: {exc}",
        )

    # --- inference -----------------------------------------------------------
    try:
        # 1. Global image inference
        inputs = _processor(images=image, return_tensors="pt")
        inputs = {k: v.to(_device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = _model(**inputs)
            logits = outputs.logits

        probabilities = F.softmax(logits, dim=-1)

        # Top-5 predictions
        top5_probs, top5_indices = torch.topk(probabilities, k=min(5, logits.size(-1)), dim=-1)

        predictions = []
        for prob, idx in zip(top5_probs[0], top5_indices[0]):
            raw_label = _model.config.id2label[idx.item()]
            predictions.append({
                "label": raw_label.replace("_", " ").title(),
                "raw_label": raw_label,
                "confidence": round(prob.item(), 4),
            })

        top = predictions[0]
        top_confidence = top["confidence"]
        top_raw_label = top["raw_label"]

        # 2. Confidence Tier Classification
        # High: score >= 0.60
        # Moderate: 0.30 <= score < 0.60
        # Low: score < 0.30 (provisional thresholds, NOT calibrated probabilities)
        if top_confidence >= 0.60:
            confidence_tier = "high"
            is_uncertain = False
            predicted_label = top["label"]
            confidence_note = (
                f"High uncalibrated model score ({top_confidence:.1%}). Visual patterns favor this Food-101 class; "
                "this score is not a probability of correctness."
            )
        elif top_confidence >= 0.30:
            confidence_tier = "moderate"
            is_uncertain = False
            predicted_label = top["label"]
            confidence_note = (
                f"Moderate uncalibrated model score ({top_confidence:.1%}). Consider alternative top-5 classes; "
                "this score is not a probability of correctness."
            )
        else:
            confidence_tier = "low"
            is_uncertain = True
            predicted_label = "Uncertain / Unsupported Food"
            confidence_note = (
                f"Low uncalibrated model score ({top_confidence:.1%} < 30.0%). The model cannot reliably classify this food. "
                "Note: Food-101 covers 101 prepared restaurant dishes and cannot reliably recognize raw produce "
                "(such as fresh apples, bananas, or raw vegetables), raw groceries, or non-food items. "
                "Please use text query search for produce nutrition."
            )

        nutrition = get_nutrition_estimate(top_raw_label)
        if is_uncertain:
            nutrition = {
                **nutrition,
                "reliability_warning": "Nutrition is provisional because the model's uncalibrated score is low. Use text search for verified nutrition.",
            }

        # 3. Multi-dish spatial arrangement analysis (with conservative confidence)
        detected_items, is_multi_item = analyze_complex_arrangement(
            image=image,
            model=_model,
            processor=_processor,
            primary_label=top_raw_label,
            device=_device,
            min_confidence=0.45,
        )

        return {
            "status": "success",
            "filename": file.filename,
            "predicted_label": predicted_label,
            "candidate_label": top["label"],
            "confidence": top["confidence"],
            "confidence_tier": confidence_tier,
            "is_uncertain": is_uncertain,
            "confidence_note": confidence_note,
            "top_5": predictions,
            "model_id": MODEL_ID,
            "is_multi_item": is_multi_item,
            "detected_items": detected_items,
            "nutrition": nutrition,
            "preprocessing": prep_meta,
        }

    except Exception as exc:
        logger.exception("Inference failed")
        raise HTTPException(
            status_code=500,
            detail=f"Inference error: {exc}",
        )
