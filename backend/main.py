import io
import logging
from contextlib import asynccontextmanager

import torch
import torch.nn.functional as F
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError
from transformers import AutoImageProcessor, AutoModelForImageClassification

from nutrition_data import get_nutrition_estimate
from routers.freshness_detector import router as freshness_router

logger = logging.getLogger("food_verse_ai")

# ---------------------------------------------------------------------------
# Model globals – populated once during application startup via the lifespan
# ---------------------------------------------------------------------------
MODEL_ID = "nateraw/food"  # ViT-base fine-tuned on Food-101 (~89 % accuracy)

_model = None
_processor = None
_model_ready = False
_model_error: str | None = None


def preprocess_image(image: Image.Image) -> tuple[Image.Image, dict]:
    """
    Activity 2.1: Preprocessing pipeline.
    - Handles EXIF orientation tags from mobile captures
    - Validates minimum dimensions and handles extreme resolutions
    - Normalizes dim/low-contrast lighting conditions via adaptive contrast adjustment
    """
    meta = {
        "exif_transposed": False,
        "contrast_enhanced": False,
        "lighting_notes": "Normal exposure & dynamic range",
    }

    # 1. EXIF orientation correction
    try:
        image = ImageOps.exif_transpose(image)
        meta["exif_transposed"] = True
    except Exception:
        meta["exif_transposed"] = False

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

    # Lighting variations handling: check mean brightness and contrast stddev
    grayscale = image.convert("L")
    stat = ImageStat.Stat(grayscale)
    mean_lum = stat.mean[0]
    std_lum = stat.stddev[0]
    meta["mean_luminance"] = round(mean_lum, 1)
    meta["contrast_stddev"] = round(std_lum, 1)

    if std_lum < 30.0 or mean_lum < 40.0:
        # Dim or low-contrast environment: apply moderate autocontrast
        image = ImageOps.autocontrast(image, cutoff=1)
        meta["contrast_enhanced"] = True
        meta["lighting_notes"] = "Enhanced contrast for low-light/dim scene"
    elif mean_lum > 220.0:
        meta["lighting_notes"] = "High brightness/overexposed lighting detected"

    return image, meta


def analyze_complex_arrangement(
    image: Image.Image,
    model,
    processor,
    primary_label: str,
    min_confidence: float = 0.20,
) -> tuple[list[dict], bool]:
    """
    Activity 2.1: Smallest suitable approach for identifying multiple food items.
    Decomposes multi-dish canvas (e.g., Indian thali, buffet platter, combo plate)
    into spatial dish zones, tests sub-regions in batched forward pass, and deduplicates
    overlapping regions to avoid double-counting nutrition.
    """
    w, h = image.size

    # Define candidate spatial zones covering quadrants and halves
    zones = [
        ("Top-Left", (0.0, 0.0, 0.65, 0.65)),
        ("Top-Right", (0.35, 0.0, 1.0, 0.65)),
        ("Bottom-Left", (0.0, 0.35, 0.65, 1.0)),
        ("Bottom-Right", (0.35, 0.35, 1.0, 1.0)),
        ("Center", (0.20, 0.20, 0.80, 0.80)),
    ]

    crops = []
    zone_boxes = []
    for name, (rx1, ry1, rx2, ry2) in zones:
        box = (int(rx1 * w), int(ry1 * h), int(rx2 * w), int(ry2 * h))
        crops.append(image.crop(box))
        zone_boxes.append((name, {"x1": rx1, "y1": ry1, "x2": rx2, "y2": ry2}))

    # Batched inference over spatial crops
    inputs = processor(images=crops, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=-1)

    top_probs, top_indices = torch.topk(probs, k=1, dim=-1)

    # Collect detections
    candidates = []
    for i, (name, box_coords) in enumerate(zone_boxes):
        conf = top_probs[i][0].item()
        idx = top_indices[i][0].item()
        raw = model.config.id2label[idx]
        display = raw.replace("_", " ").title()

        if conf >= min_confidence:
            candidates.append({
                "raw_label": raw,
                "label": display,
                "confidence": round(conf, 4),
                "region": name,
                "box": box_coords,
            })

    # Deduplication across overlapping regions:
    # If multiple zones detect the same dish, keep only the highest-confidence occurrence
    unique_dishes = {}
    for item in candidates:
        lbl = item["raw_label"]
        if lbl not in unique_dishes or item["confidence"] > unique_dishes[lbl]["confidence"]:
            unique_dishes[lbl] = item

    distinct_items = list(unique_dishes.values())
    distinct_items.sort(key=lambda x: x["confidence"], reverse=True)

    # An arrangement is multi-item if >= 2 distinct dishes are confidently recognized
    is_multi_item = len(distinct_items) >= 2

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
    """Load the food-recognition model at startup, release on shutdown."""
    global _model, _processor, _model_ready, _model_error

    try:
        logger.info("Loading food-recognition model '%s' …", MODEL_ID)
        _processor = AutoImageProcessor.from_pretrained(MODEL_ID)
        _model = AutoModelForImageClassification.from_pretrained(MODEL_ID)
        _model.eval()
        _model_ready = True
        logger.info("Model loaded successfully.")
    except Exception as exc:
        _model_error = str(exc)
        logger.error("Failed to load model: %s", _model_error)

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
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(freshness_router)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model_ready": _model_ready,
        "model_id": MODEL_ID,
    }


@app.get("/api/v1/food/nutrition")
def get_food_nutrition(food: str):
    """Retrieve estimated reference nutrition facts for a given food label."""
    return get_nutrition_estimate(food)


@app.post("/api/v1/food/recognize")
async def recognize_food(file: UploadFile = File(...)):
    # --- guard: model must be loaded ----------------------------------------
    if not _model_ready:
        raise HTTPException(
            status_code=503,
            detail=f"Model is not available. {_model_error or 'Still loading…'}",
        )

    # --- guard: content-type must be image -----------------------------------
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a valid image file (PNG, JPG, WEBP).",
        )

    # --- read & decode image with preprocessing ------------------------------
    try:
        raw_bytes = await file.read()
        raw_image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        image, prep_meta = preprocess_image(raw_image)
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
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading image: {exc}",
        )

    # --- inference -----------------------------------------------------------
    try:
        # 1. Global image inference
        inputs = _processor(images=image, return_tensors="pt")

        with torch.no_grad():
            outputs = _model(**inputs)
            logits = outputs.logits

        probabilities = F.softmax(logits, dim=-1)

        # Top-5 predictions
        top5_probs, top5_indices = torch.topk(probabilities, k=min(5, logits.size(-1)), dim=-1)

        predictions = []
        for prob, idx in zip(top5_probs[0], top5_indices[0]):
            label = _model.config.id2label[idx.item()]
            predictions.append({
                "label": label.replace("_", " ").title(),
                "confidence": round(prob.item(), 4),
            })

        top = predictions[0]
        top_raw_label = _model.config.id2label[top5_indices[0][0].item()]
        nutrition = get_nutrition_estimate(top_raw_label)

        # 2. Multi-dish spatial arrangement analysis
        detected_items, is_multi_item = analyze_complex_arrangement(
            image=image,
            model=_model,
            processor=_processor,
            primary_label=top_raw_label,
            min_confidence=0.20,
        )

        return {
            "status": "success",
            "filename": file.filename,
            "predicted_label": top["label"],
            "confidence": top["confidence"],
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
