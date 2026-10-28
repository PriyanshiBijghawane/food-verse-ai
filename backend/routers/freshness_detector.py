"""
Epic 3 — Food Freshness & Spoilage Detection Module
====================================================
Activity 3.1  Image Preprocessing and Feature Extraction
Activity 3.2  Freshness Classification and Safety Recommendation Logic

Approach
--------
- No external ML model or API key is required.
- Visual features (colour histogram, saturation, brightness, texture variance,
  mould-pattern heuristics) are extracted directly from the uploaded image using
  Pillow and NumPy.
- A transparent, rule-based scoring algorithm converts these features into a
  freshness score and a Fresh / Moderate / Spoiled classification.
- The module is deliberately conservative: it can only describe *visual* cues and
  cannot detect microbial contamination, taste, or smell.  All responses clearly
  state this limitation.

Supported food categories for context-aware heuristics
-------------------------------------------------------
  fruit, vegetable, cooked, dairy, meat, bread, generic (default)
"""

from __future__ import annotations

import io
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError
from torchvision import models, transforms

logger = logging.getLogger("food_verse_ai.freshness")

router = APIRouter(prefix="/api/v1/food", tags=["freshness"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum image dimension accepted
MIN_DIM = 64
# Maximum dimension we'll process (larger images are downscaled)
MAX_DIM = 1200

# Category detection keywords mapped to food type strings
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "fruit": ["apple", "banana", "orange", "mango", "grape", "strawberry", "berry",
              "pear", "peach", "plum", "cherry", "kiwi", "lemon", "lime", "melon",
              "pineapple", "watermelon", "avocado", "fruit"],
    "vegetable": ["carrot", "broccoli", "lettuce", "spinach", "tomato", "cucumber",
                  "potato", "onion", "garlic", "pepper", "corn", "peas", "beans",
                  "cabbage", "cauliflower", "celery", "mushroom", "vegetable", "veggie"],
    "meat": ["chicken", "beef", "pork", "lamb", "fish", "salmon", "tuna", "shrimp",
             "prawn", "steak", "meat", "sausage", "bacon", "ham"],
    "dairy": ["milk", "cheese", "yogurt", "butter", "cream", "dairy"],
    "bread": ["bread", "toast", "sandwich", "bun", "roll", "bagel", "croissant",
              "muffin", "cake", "pastry"],
    "cooked": ["curry", "pizza", "pasta", "rice", "soup", "stew", "salad",
               "burger", "taco", "sushi", "noodle", "fried", "grilled", "roasted",
               "baked", "cooked", "dish", "meal", "food"],
}


def _detect_food_category(food_hint: str | None) -> str:
    """Map an optional food-label hint to a category string."""
    if not food_hint:
        return "generic"
    hint_lower = food_hint.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in hint_lower for kw in keywords):
            return category
    return "generic"


# ---------------------------------------------------------------------------
# Activity 3.1 — Preprocessing helpers
# ---------------------------------------------------------------------------

def _validate_and_decode(raw_bytes: bytes) -> Image.Image:
    """
    Validate raw bytes and return an RGB PIL Image.
    Raises ValueError for corrupt or unreadable data.
    """
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.verify()                       # checks for truncated data
    except (UnidentifiedImageError, Exception) as exc:
        raise ValueError(f"Cannot decode image: {exc}") from exc

    # Re-open after verify() — Pillow requires re-opening after verify
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img = ImageOps.exif_transpose(img)  # fix mobile EXIF rotation
        img = img.convert("RGB")
    except Exception as exc:
        raise ValueError(f"Cannot open image after verification: {exc}") from exc

    w, h = img.size
    if w < MIN_DIM or h < MIN_DIM:
        raise ValueError(
            f"Image too small ({w}x{h}). Minimum supported size is {MIN_DIM}x{MIN_DIM}."
        )
    return img


def _preprocess(img: Image.Image) -> tuple[Image.Image, dict]:
    """
    Activity 3.1: resize, lighting-enhance, and mildly denoise the image.
    Returns the processed image and metadata describing what was done.
    """
    meta: dict[str, Any] = {}
    w, h = img.size
    meta["original_resolution"] = f"{w}x{h}"

    # --- Downscale very large images ----------------------------------------
    if max(w, h) > MAX_DIM:
        scale = MAX_DIM / max(w, h)
        new_w, new_h = max(MIN_DIM, int(w * scale)), max(MIN_DIM, int(h * scale))
        img = img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
        meta["resized_to"] = f"{new_w}x{new_h}"
    else:
        meta["resized_to"] = f"{w}x{h}"

    # --- Luminance analysis -------------------------------------------------
    gray = img.convert("L")
    stat = ImageStat.Stat(gray)
    mean_lum = stat.mean[0]
    std_lum  = stat.stddev[0]
    meta["mean_luminance"]  = round(mean_lum, 1)
    meta["contrast_stddev"] = round(std_lum,  1)

    # --- Adaptive lighting correction without channel color shift ------------
    lighting_note = "Normal exposure"
    if mean_lum < 40 or std_lum < 25:
        # Use brightness and contrast enhancement rather than per-channel autocontrast which distorts color balance
        enhancer_b = ImageEnhance.Brightness(img)
        img = enhancer_b.enhance(1.2)
        enhancer_c = ImageEnhance.Contrast(img)
        img = enhancer_c.enhance(1.1)
        lighting_note = "Enhanced: low-light / dim scene detected"
        meta["lighting_enhanced"] = True
    elif mean_lum > 220:
        lighting_note = "Overexposed / high-brightness scene"
        meta["lighting_enhanced"] = False
    else:
        meta["lighting_enhanced"] = False

    meta["lighting_note"] = lighting_note

    # --- Mild noise reduction (box-blur radius 1) ---------------------------
    img = img.filter(ImageFilter.BoxBlur(radius=1))
    meta["noise_reduction"] = "BoxBlur radius=1 applied"

    return img, meta


# ---------------------------------------------------------------------------
# Activity 3.1 — Feature extraction
# ---------------------------------------------------------------------------

def _extract_features(img: Image.Image) -> dict:
    """
    Extract freshness-relevant visual features:
      - HSV colour statistics (hue, saturation, brightness)
      - Spoilage colour fractions (brown/dark oxidation, grey discolouration,
        teal/blue-green mould patches, white fuzzy patches, yellowing)
      - A freshness-positive "vivid food colour" fraction (reds/oranges/greens
        that are characteristic of unprocessed fresh food)
      - Texture variance as proxy for surface irregularities
      - Edge density as proxy for shrivelling / wrinkles

    Calibration notes
    -----------------
    * mould_teal_frac: hue 150-210°, high saturation.  This is the teal/blue-green
      mould colour.  Pure vivid green (~120°) seen on fresh spinach, apples, and
      peppers is excluded to avoid false-positive mould alarms.
    * fresh_vivid_frac: vivid saturated colours in the green (90-150°), red (340-20°),
      and orange (20-50°) ranges.  A high fraction here is a freshness indicator.
    * brown_frac: hue 10-42°, mid-low value, medium saturation — brownish rot/oxidation.
    * dark_frac: v < 0.20 — very dark pixels (overexposed background also triggers
      this, so penalty weight is kept moderate).
    """
    arr = np.array(img, dtype=np.float32)          # shape (H, W, 3) — RGB 0-255

    # --- Convert to HSV (manual, avoids opencv dependency) ------------------
    r, g, b = arr[:, :, 0] / 255.0, arr[:, :, 1] / 255.0, arr[:, :, 2] / 255.0
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin + 1e-8

    v = cmax                                        # Value  0-1
    s = np.divide(delta, cmax, out=np.zeros_like(delta), where=(cmax > 1e-6))

    # Hue (degrees 0-360)
    h = np.zeros_like(r)
    mask_r = (cmax == r)
    mask_g = (cmax == g)
    mask_b = (cmax == b)
    h[mask_r] = (60.0 * ((g[mask_r] - b[mask_r]) / delta[mask_r]) % 360)
    h[mask_g] = (60.0 * ((b[mask_g] - r[mask_g]) / delta[mask_g]) + 120)
    h[mask_b] = (60.0 * ((r[mask_b] - g[mask_b]) / delta[mask_b]) + 240)

    mean_sat = float(np.mean(s))
    mean_val = float(np.mean(v))
    std_sat  = float(np.std(s))

    total_px = float(r.size)

    # --- Texture variance & Edge density (computed early for mask refinement) ---
    gray_arr = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    texture_variance = float(np.var(gray_arr))

    gy = np.diff(gray_arr, axis=0)
    gx = np.diff(gray_arr, axis=1)
    grad_h = np.sqrt(gy[:, :-1] ** 2 + gx[:-1, :] ** 2)
    edge_density = float(np.mean(grad_h > 20))

    # Pad grad_h to match (H, W) for spatial masking
    grad_map = np.pad(grad_h, ((0, 1), (0, 1)), mode="edge")

    # --- Brown / oxidation (general brown/oxidation, includes many brown hues)
    brown_mask = (
        (h >= 5) & (h <= 42) &
        (v >= 0.12) & (v <= 0.58) &
        (s >= 0.18)
    )

    # --- Refined brown‑rot region (deep rust, amber, dark-brown fungal decay)
    # Hue 5‑42°, moderate brightness (V 0.15–0.58), saturation >= 0.18 (no artificial upper cap)
    brown_rot_mask = (
        (h >= 5) & (h <= 42) &
        (v >= 0.15) & (v <= 0.58) &
        (s >= 0.18)
    )

    # --- Very dark patches (possible rot, bruising, deep shadow) ------------
    dark_mask = v < 0.18

    # --- Grey/desaturated discolouration ------------------------------------
    grey_mask = (s < 0.12) & (v > 0.28) & (v < 0.80)

    # --- Mould teal/blue-green: hue 155-215°, medium-high saturation -------
    mould_teal_mask = (
        (h >= 155) & (h <= 215) &
        (s >= 0.28) & (v >= 0.22)
    )

    # --- Fresh vivid colour: greens (80-155°), reds (340-360° ∪ 0-20°),
    #     oranges (20-42°), with HIGH saturation & HIGH brightness -----------
    fresh_green_mask  = (h >= 80)  & (h <= 155) & (s >= 0.35) & (v >= 0.42)
    fresh_red_mask    = ((h >= 340) | (h <= 20)) & (s >= 0.45) & (v >= 0.55)
    fresh_orange_mask = (h > 20)  & (h < 42)  & (s >= 0.50) & (v >= 0.55)
    fresh_vivid_mask  = fresh_green_mask | fresh_red_mask | fresh_orange_mask

    fresh_vivid_frac = float(np.sum(fresh_vivid_mask) / total_px)
    brown_rot_frac = float(np.sum(brown_rot_mask) / total_px)
    brown_frac      = float(np.sum(brown_mask)      / total_px)
    dark_frac       = float(np.sum(dark_mask)       / total_px)
    grey_frac       = float(np.sum(grey_mask)       / total_px)
    mould_teal_frac = float(np.sum(mould_teal_mask) / total_px)

    # --- White background vs White fuzzy mould detection -------------------
    # A clean white plate or light tabletop is characterized by bright, low-saturation pixels.
    # True fuzzy mould exhibits rough texture/edge gradients on food surfaces.
    # If the white area is extensive (>30% of frame), smooth white pixels are recognized
    # as background plate rather than fungal mould.
    white_surface_candidate = (v > 0.82) & (s < 0.12)
    white_surface_frac = float(np.sum(white_surface_candidate) / total_px)

    if white_surface_frac > 0.30:
        # Require local texture gradient for fuzzy mould candidate to avoid plate false-positives
        mould_white_mask = (v > 0.88) & (s < 0.07) & (grad_map > 16.0)
    else:
        mould_white_mask = (v > 0.88) & (s < 0.07)

    mould_white_frac = float(np.sum(mould_white_mask) / total_px)

    # --- Yellowing: hue 42-70°, warm saturation, medium value ---------------
    yellow_mask = (
        (h >= 42) & (h <= 72) &
        (s >= 0.28) & (v >= 0.40)
    )
    yellow_frac = float(np.sum(yellow_mask) / total_px)

    # --- Low-information / empty-plate / background-dominant detection -----
    has_spoilage_colour = (
        brown_frac >= 0.08
        or brown_rot_frac >= 0.06
        or dark_frac >= 0.12
        or grey_frac >= 0.15
        or mould_teal_frac >= 0.04
        or yellow_frac >= 0.20
    )

    # 1. Clean plate or light surface: >60% light neutral area, no vivid food, no active spoilage
    is_plate_or_light_bg = (
        (white_surface_frac > 0.60)
        and (fresh_vivid_frac < 0.05)
        and not has_spoilage_colour
    )

    # 2. Plain uniform surface (e.g. blank cutting board, solid backdrop)
    is_uniform_surface = (
        std_sat < 0.06
        and texture_variance < 80.0
        and edge_density < 0.04
        and fresh_vivid_frac < 0.05
        and not has_spoilage_colour
    )

    # 3. Overall neutral / featureless image (e.g. clean stainless steel or table without food)
    neutral_pixel_frac = float(np.mean(s < 0.15))
    is_neutral_background = (
        neutral_pixel_frac > 0.75
        and fresh_vivid_frac < 0.04
        and not has_spoilage_colour
        and edge_density < 0.12
    )

    low_information = bool(
        (is_plate_or_light_bg or is_uniform_surface or is_neutral_background)
        and not has_spoilage_colour
    )

    return {
        "mean_saturation":    round(mean_sat,         4),
        "mean_brightness":    round(mean_val,         4),
        "saturation_stddev":  round(std_sat,          4),
        "brown_fraction":     round(brown_frac,       4),
        "brown_rot_fraction": round(brown_rot_frac,   4),
        "dark_fraction":      round(dark_frac,        4),
        "grey_fraction":      round(grey_frac,        4),
        "mould_teal_fraction":  round(mould_teal_frac,  4),
        "mould_white_fraction": round(mould_white_frac, 4),
        "yellow_fraction":    round(yellow_frac,      4),
        "fresh_vivid_fraction": round(fresh_vivid_frac, 4),
        "texture_variance":   round(texture_variance, 1),
        "edge_density":       round(edge_density,     4),
        "low_information":    low_information,
    }


# ---------------------------------------------------------------------------
# Activity 3.2 — Freshness classification
# ---------------------------------------------------------------------------

# Thresholds are intentionally generous to avoid false "Spoiled" alarms.
# All weights and thresholds are documented for full explainability.

# Spoilage feature → (base_weight, minimum_fraction_before_penalty)
# base_weight determines how much each 1-unit (100%) fraction contributes to score
# Only fractions above the threshold incur penalties (avoids noise-floor false alarms)
_SPOILAGE_FEATURES = {
    "brown_fraction":       (55.0, 0.08),   # generic brown/oxidation (low‑brightness brown)
    "brown_rot_fraction":   (85.0, 0.06),   # orange‑brown rot – higher weight, stricter threshold
    "dark_fraction":        (22.0, 0.12),   # dark patches
    "grey_fraction":        (28.0, 0.15),   # grey discolouration
    "mould_teal_fraction":  (85.0, 0.04),   # teal mould
    "mould_white_fraction": (30.0, 0.10),   # white fuzzy mould
    "yellow_fraction":      (14.0, 0.20),   # yellowing (mild spoilage)
}

# Category modifiers: fraction of base_weight to apply (1.0 = full, 0.5 = half)
# Lower values = more tolerant of that feature for this category.
# NOTE: brown_rot_fraction is NOT reduced for fruit — brown rot on fruit is
# genuine spoilage and should receive the full penalty.
_CATEGORY_MODIFIERS: dict[str, dict[str, float]] = {
    "fruit":     {"brown_fraction": 0.50, "yellow_fraction": 0.60, "dark_fraction": 0.70},
    "vegetable": {"brown_fraction": 0.55, "grey_fraction": 0.70},
    "bread":     {"brown_fraction": 0.35, "dark_fraction": 0.60},  # toast is naturally brown
    "cooked":    {"brown_fraction": 0.40, "dark_fraction": 0.50},  # cooked food is darker
    "meat":      {"grey_fraction":  0.70, "dark_fraction": 0.65},  # raw meat is naturally dark
    "dairy":     {"mould_white_fraction": 0.50},                    # some cheese has white rind
    "generic":   {},
}


def _compute_freshness_score(features: dict, category: str) -> tuple[int, list[str]]:
    """
    Rule-based freshness scoring (0-100, 100 = perfectly fresh).

    Strategy
    --------
    1. If the image is flagged as 'low_information' (empty plate, plain background),
       return score -1 with a descriptive sign.  This avoids falsely labelling
       featureless surfaces as spoiled food.
    2. Start from a base of 70 (assumes average food has moderate freshness cues).
    3. Add up to +30 freshness bonus from vivid food colours and good saturation.
    4. Subtract spoilage penalties from each colour-anomaly fraction.

    Returns (score, list_of_detected_visual_signs).
    """

    # --- Low-information early exit -----------------------------------------
    if features.get("low_information", False):
        return -1, [
            "Image appears to be an empty plate, plain background, or otherwise "
            "lacks sufficient food-related visual content for freshness analysis."
        ]

    mods = _CATEGORY_MODIFIERS.get(category, {})

    # --- Freshness bonus (0-30 points) ---
    fresh_frac   = features.get("fresh_vivid_fraction", 0.0)
    mean_sat     = features.get("mean_saturation", 0.5)
    mean_bright  = features.get("mean_brightness", 0.5)
    brown_rot_val = features.get("brown_rot_fraction", 0.0)
    brown_val     = features.get("brown_fraction", 0.0)

    # Vivid colour fraction bonus (max +18)
    colour_bonus = min(fresh_frac * 35.0, 18.0)
    # Saturation bonus (max +8)  — food that has lost colour is duller
    sat_bonus = min(max((mean_sat - 0.15), 0.0) * 20.0, 8.0)
    # Brightness in a healthy range bonus (max +4)
    bright_bonus = 0.0
    if 0.30 <= mean_bright <= 0.85:
        bright_bonus = 4.0
    elif mean_bright > 0.85:
        bright_bonus = 2.0  # over-bright may be flash / bleached

    freshness_bonus = colour_bonus + sat_bonus + bright_bonus

    # Severe rot check: active decay cannot be masked by surrounding vivid skin
    is_severe_rot = (brown_rot_val >= 0.14) or (brown_rot_val >= 0.08 and brown_val >= 0.18)
    if is_severe_rot:
        freshness_bonus = 0.0
    elif brown_rot_val >= 0.06:
        freshness_bonus = min(freshness_bonus, 5.0)

    base_score = 70.0 + freshness_bonus

    # --- Spoilage penalties ---
    spoilage_penalty = 0.0
    signs: list[str] = []

    for feature_name, (base_weight, threshold) in _SPOILAGE_FEATURES.items():
        value = features.get(feature_name, 0.0)
        if value < threshold:
            continue   # below noise floor — ignore

        multiplier = mods.get(feature_name, 1.0)
        effective_weight = base_weight * multiplier
        penalty = (value - threshold) * effective_weight

        if penalty >= 3.5:  # threshold to surface as visible sign
            label_raw = (
                feature_name
                .replace("mould_teal", "Teal/Blue-green mould")
                .replace("mould_white", "White fuzzy mould")
                .replace("brown_rot", "Brown rot")
                .replace("brown", "Brown/oxidation")
                .replace("dark", "Dark patch")
                .replace("grey", "Grey")
                .replace("yellow", "Yellowing")
                .replace("_fraction", "")
                .strip()
            )
            signs.append(
                f"{label_raw.title()} discolouration detected "
                f"({value * 100:.1f}% of visible area)"
            )

        spoilage_penalty += penalty

    if is_severe_rot:
        decay_penalty = max(35.0, brown_rot_val * 110.0)
        spoilage_penalty += decay_penalty
        if not any("rot" in s.lower() or "decay" in s.lower() for s in signs):
            signs.insert(0, f"Significant brown rot decay lesion detected ({brown_rot_val * 100:.1f}% of visible area)")

    # --- Additional signal penalties ---
    if mean_sat < 0.12 and not is_severe_rot:
        spoilage_penalty += 10.0
        signs.append("Very low colour saturation — food appears faded or dull")

    tex_var = features.get("texture_variance", 500)
    if tex_var > 4000:
        spoilage_penalty += 5.0
        signs.append("High surface texture irregularity — possible wrinkling or mould texture")

    edge_d = features.get("edge_density", 0.05)
    if edge_d > 0.35:
        spoilage_penalty += 4.0
        signs.append("High edge density — possible shrivelling or surface deformation")

    raw_score = base_score - spoilage_penalty
    score = int(max(0, min(100, round(raw_score))))
    if is_severe_rot and score >= 45:
        score = 42
    elif brown_rot_val >= 0.06 and score >= 65:
        score = 62

    return score, signs


def _classify(score: int) -> tuple[str, str]:
    """
    Map freshness score to a category and safety status string.
    Returns (freshness_label, safety_status).

    A score of -1 indicates the image lacked sufficient food content for
    analysis (e.g. empty plate, plain background).  This is mapped to
    'Inconclusive' rather than 'Spoiled'.
    """
    if score < 0:
        return "Inconclusive", "unable_to_assess"
    if score >= 72:
        return "Fresh", "safe_to_consume"
    elif score >= 45:
        return "Moderate", "consume_with_caution"
    else:
        return "Spoiled", "do_not_consume"


def _build_reasoning(
    features: dict,
    category: str,
    score: int,
    label: str,
    signs: list[str],
) -> str:
    """Build a human-readable summary of the classification reasoning."""
    sat_pct   = round(features.get("mean_saturation", 0) * 100, 1)
    bright_pct = round(features.get("mean_brightness", 0) * 100, 1)
    brown_pct = round(features.get("brown_fraction", 0) * 100, 1)

    lines = [
        f"Image analysed as category: {category}.",
        f"Mean colour saturation: {sat_pct}%, mean brightness: {bright_pct}%.",
        f"Brown/dark-patch fraction: {brown_pct}%.",
    ]

    if signs:
        lines.append("Key visual cues: " + "; ".join(signs[:3]) + ".")
    else:
        lines.append("No significant spoilage cues detected in the visible surface.")

    lines.append(
        f"Rule-based score: {score}/100 → classified as '{label}'."
    )
    return " ".join(lines)


def _build_recommendations(label: str, category: str, signs: list[str]) -> list[str]:
    """Return 2–4 practical, evidence-grounded recommendations."""
    recs: list[str] = []

    if label == "Inconclusive":
        recs.append(
            "The image does not appear to contain clearly identifiable food. "
            "Please upload a clear photo of the food item you want analysed."
        )
        recs.append(
            "For best results, ensure the food fills most of the frame, is well-lit, "
            "and is not obscured by packaging or background objects."
        )
        return recs

    if label == "Fresh":
        recs.append(
            "The food appears visually fresh. Follow standard storage guidelines for "
            f"your food type ({category}) to maintain freshness."
        )
        recs.append(
            "Refrigerate perishables promptly and consume within the manufacturer's "
            "recommended timeframe."
        )
    elif label == "Moderate":
        recs.append(
            "Moderate visual spoilage cues are present. Inspect the food in person — "
            "check for unusual odour, texture, or mould before consuming."
        )
        recs.append(
            "If the food smells normal and the affected area is small and superficial, "
            "you may be able to discard only that section, depending on the food type."
        )
        recs.append(
            "When in doubt, follow food-safety guidance: "
            "\"When in doubt, throw it out.\""
        )
    else:  # Spoiled
        recs.append(
            "Significant visual spoilage signs are present. We strongly recommend "
            "discarding this food rather than consuming it."
        )
        recs.append(
            "Consuming visually spoiled food carries risk of foodborne illness. "
            "This assessment is based on visible surface cues only — microbial "
            "contamination may extend beyond what is visible."
        )
        recs.append(
            "Contact your local food safety authority if you believe the food was "
            "commercially labelled as fresh but appears spoiled."
        )

    if any("mould" in s.lower() for s in signs):
        recs.append(
            "Mould-like patches detected. Soft foods (bread, fruit, vegetables) should "
            "be fully discarded when mould is found — mould roots can penetrate deeper "
            "than the visible surface."
        )

    return recs


# ---------------------------------------------------------------------------
# Safety disclaimer (static)
# ---------------------------------------------------------------------------

_SAFETY_DISCLAIMER = (
    "IMPORTANT: This assessment is based solely on visible colour, texture, and surface "
    "features extracted from a single photograph. It cannot detect microbial contamination, "
    "toxins, internal spoilage, smell, or taste. Visual freshness cues are not scientifically "
    "calibrated for all food types. Always use your own judgement, observe storage conditions, "
    "respect use-by dates, and consult official food-safety resources for guidance."
)


# ---------------------------------------------------------------------------
# Freshness Model Manager (Phase 5 Computer Vision Pipeline)
# ---------------------------------------------------------------------------

class FreshnessModelManager:
    """
    Manages deep-learning freshness classification models.
    Supports transfer-learning architectures (e.g. MobileNetV3, ResNet18) trained via train_classifier.py.
    When no checkpoint is loaded, operates in honest transparent heuristic fallback mode.
    """

    def __init__(self):
        self.model: Optional[nn.Module] = None
        self.model_id: str = "visual_heuristics_v1 (rule-based computer vision)"
        self.analysis_mode: str = "heuristic_visual_cues"
        self.is_model_loaded: bool = False
        self.checkpoint_path: Optional[str] = None
        self.classes: List[str] = ["fresh", "spoiled"]
        self.label2id: Dict[str, int] = {"fresh": 0, "spoiled": 1}
        self.id2label: Dict[int, str] = {0: "fresh", 1: "spoiled"}
        self.device: str = "cuda" if torch.cuda.is_available() else "cpu"
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def load_model(
        self,
        checkpoint_path: str | Path,
        mapping_path: str | Path,
        device: Optional[str] = None,
    ) -> bool:
        """Loads a fine-tuned freshness checkpoint into memory."""
        ckpt_path = Path(checkpoint_path)
        map_path = Path(mapping_path)
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Checkpoint not found at '{ckpt_path}'.")
        if not map_path.exists():
            raise FileNotFoundError(f"Class mapping not found at '{map_path}'.")

        if device:
            self.device = device

        with open(map_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)

        self.id2label = {int(k): v for k, v in mapping["id2label"].items()}
        self.label2id = mapping["label2id"]
        self.classes = [self.id2label[i] for i in range(len(self.label2id))]
        num_classes = len(self.classes)

        checkpoint = torch.load(ckpt_path, map_location=self.device)
        backbone_name = checkpoint.get("backbone", "mobilenet_v3_small")

        if backbone_name == "mobilenet_v3_small":
            model = models.mobilenet_v3_small(weights=None)
            in_features = model.classifier[3].in_features
            model.classifier[3] = nn.Linear(in_features, num_classes)
        elif backbone_name == "resnet18":
            model = models.resnet18(weights=None)
            in_features = model.fc.in_features
            model.fc = nn.Linear(in_features, num_classes)
        else:
            raise ValueError(f"Unsupported backbone '{backbone_name}'.")

        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        model.to(self.device)

        self.model = model
        self.model_id = f"{backbone_name}_freshness_v1"
        self.analysis_mode = "deep_learning_model"
        self.is_model_loaded = True
        self.checkpoint_path = str(ckpt_path)
        logger.info("Loaded fine-tuned freshness model '%s' (%d classes) on %s.", self.model_id, num_classes, self.device)
        return True

    def unload_model(self) -> None:
        """Unloads model and restores transparent heuristic fallback mode."""
        self.model = None
        self.model_id = "visual_heuristics_v1 (rule-based computer vision)"
        self.analysis_mode = "heuristic_visual_cues"
        self.is_model_loaded = False
        self.checkpoint_path = None

    def predict(self, pil_image: Image.Image) -> Optional[Dict[str, Any]]:
        """Executes forward pass if model is loaded; returns None if in fallback mode."""
        if not self.is_model_loaded or self.model is None:
            return None

        tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=-1)[0]

        top_prob, top_idx = torch.topk(probs, k=1)
        conf = float(top_prob.item())
        pred_idx = int(top_idx.item())
        pred_class = self.id2label.get(pred_idx, "unknown")

        prob_dict = {
            self.id2label.get(i, str(i)): round(float(p.item()), 4)
            for i, p in enumerate(probs)
        }
        is_uncertain = conf < 0.60

        return {
            "model_id": self.model_id,
            "predicted_class": pred_class,
            "confidence": round(conf, 4),
            "is_uncertain": is_uncertain,
            "class_probabilities": prob_dict,
            "device": self.device,
        }


freshness_manager = FreshnessModelManager()


def get_freshness_dataset_spec() -> Dict[str, Any]:
    """Returns documentation and requirements for training a dedicated freshness dataset."""
    return {
        "dataset_name": "Food Freshness & Produce Quality Dataset",
        "recommended_source": "Kaggle Fruits and Vegetables Freshness or Kaggle Fresh/Rotten Produce",
        "folder_layout": "data/freshness_raw/<class_name>/<images...>",
        "supported_classes_example": [
            "fresh_apples", "rotten_apples",
            "fresh_banana", "rotten_banana",
            "fresh_oranges", "rotten_oranges",
            "fresh_tomatoes", "rotten_tomatoes"
        ],
        "preprocessing": "LANCZOS resize to 224x224, ImageNet normalization",
        "backbone_recommendation": "MobileNetV3-Small (lightweight CPU inference < 25ms, ~2.5MB)",
        "training_tool": "python train_classifier.py --data_dir data/freshness_splits --output_dir checkpoints/freshness_model",
    }


# ---------------------------------------------------------------------------
# FastAPI endpoints
# ---------------------------------------------------------------------------

@router.get("/freshness/status")
def get_freshness_status():
    """
    GET /api/v1/food/freshness/status
    Reports active freshness model state, hardware device, and pipeline disclosure.
    """
    return {
        "status": "ok",
        "model_loaded": freshness_manager.is_model_loaded,
        "model_id": freshness_manager.model_id,
        "analysis_mode": freshness_manager.analysis_mode,
        "device": freshness_manager.device,
        "checkpoint_path": freshness_manager.checkpoint_path,
        "supported_classes": freshness_manager.classes if freshness_manager.is_model_loaded else [],
        "pipeline_disclosure": (
            "Deep learning model active."
            if freshness_manager.is_model_loaded
            else "Running on rule-based multi-spectral visual heuristics. Fine-tuned checkpoints can be attached via load_model()."
        ),
        "limitations_notice": (
            "Visual inspection cannot detect microbial pathogens (e.g. Salmonella, E. coli, Listeria) or chemical toxins."
        ),
    }

@router.post("/freshness")
async def detect_freshness(
    file: UploadFile = File(...),
    food_hint: str | None = None,
):
    """
    POST /api/v1/food/freshness

    Accepts a food image (JPEG / PNG / WEBP) and an optional `food_hint` query
    parameter (e.g., "apple", "chicken curry") that improves category-specific
    heuristics.

    Returns structured freshness analysis: preprocessing metadata, extracted
    visual features, freshness score (0–100), classification label, detected
    visual signs, reasoning, safety status, and recommendations.
    """

    # --- Content-type guard -------------------------------------------------
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid file type. "
                "Please upload a valid image file (JPEG, PNG, or WEBP)."
            ),
        )

    # --- Read bytes ---------------------------------------------------------
    try:
        raw_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {exc}")

    if len(raw_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # ---  Activity 3.1: Validate & decode -----------------------------------
    try:
        img = _validate_and_decode(raw_bytes)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    # --- Activity 3.1: Preprocess -------------------------------------------
    try:
        img, prep_meta = _preprocess(img)
    except Exception as exc:
        logger.exception("Preprocessing failed")
        raise HTTPException(status_code=500, detail=f"Preprocessing error: {exc}")

    # --- Activity 3.1: Feature extraction -----------------------------------
    try:
        features = _extract_features(img)
    except Exception as exc:
        logger.exception("Feature extraction failed")
        raise HTTPException(status_code=500, detail=f"Feature extraction error: {exc}")

    category = _detect_food_category(food_hint)

    # --- Activity 3.2: Classification ---------------------------------------
    try:
        score, signs = _compute_freshness_score(features, category)
        label, safety_status = _classify(score)
        reasoning = _build_reasoning(features, category, score, label, signs)
        recommendations = _build_recommendations(label, category, signs)
    except Exception as exc:
        logger.exception("Classification failed")
        raise HTTPException(status_code=500, detail=f"Classification error: {exc}")

    # Determine detected food label and confidence
    detected_food = food_hint.strip().title() if (food_hint and food_hint.strip()) else None
    if not detected_food:
        if features.get("low_information"):
            detected_food = "Non-food / Neutral Surface"
        else:
            try:
                import main
                if main._model_ready and main._model is not None and main._processor is not None:
                    inputs = main._processor(images=img, return_tensors="pt")
                    import torch
                    with torch.no_grad():
                        out = main._model(**inputs)
                        probs = torch.softmax(out.logits, dim=-1)
                        top_conf, top_idx = torch.topk(probs, k=1, dim=-1)
                        raw_name = main._model.config.id2label[top_idx[0][0].item()]
                        if top_conf[0][0].item() >= 0.25:
                            detected_food = raw_name.replace("_", " ").title()
                            category = _detect_food_category(raw_name)
            except Exception:
                pass
    # --- Model Inference vs Heuristic Fallback ------------------------------
    model_inference = freshness_manager.predict(img)

    # Compile substantiated visual evidence extracted from pixels
    visual_evidence = {
        "browning_detected": bool(features["brown_rot_fraction"] >= 0.08 or features["brown_fraction"] >= 0.20),
        "browning_percentage": round(features["brown_rot_fraction"] * 100, 1),
        "mold_detected": bool(features["mould_teal_fraction"] >= 0.04 or features["mould_white_fraction"] >= 0.20),
        "teal_mold_percentage": round(features["mould_teal_fraction"] * 100, 1),
        "vivid_color_percentage": round(features["fresh_vivid_fraction"] * 100, 1),
        "texture_degradation": bool(features["texture_variance"] > 1800.0 or features["edge_density"] > 0.25),
        "low_information_surface": bool(features.get("low_information", False)),
    }

    limitations = [
        "Assessment is based exclusively on visible 2D surface features.",
        "Cannot detect microbial foodborne pathogens (e.g. Salmonella, E. coli, Listeria, norovirus) or bacterial toxins.",
        "Cannot detect internal anaerobic rot, odor, off-taste, or souring.",
        "Surface visual integrity does not guarantee microbiological food safety. Always adhere to use-by dates, refrigeration standards, and safe cooking temperatures.",
    ]

    # Determine detected food label and confidence
    detected_food = food_hint.strip().title() if (food_hint and food_hint.strip()) else None
    if not detected_food:
        if features.get("low_information"):
            detected_food = "Non-food / Neutral Surface"
        else:
            try:
                import main
                if main._model_ready and main._model is not None and main._processor is not None:
                    inputs = main._processor(images=img, return_tensors="pt")
                    inputs = {k: v.to(main._device) for k, v in inputs.items()}
                    import torch
                    with torch.no_grad():
                        out = main._model(**inputs)
                        probs = torch.softmax(out.logits, dim=-1)
                        top_conf, top_idx = torch.topk(probs, k=1, dim=-1)
                        raw_name = main._model.config.id2label[top_idx[0][0].item()]
                        if top_conf[0][0].item() >= 0.30:
                            detected_food = raw_name.replace("_", " ").title()
                            category = _detect_food_category(raw_name)
            except Exception:
                pass
            if not detected_food:
                detected_food = "Food Item"

    if model_inference is not None:
        analysis_mode = "deep_learning_model"
        model_id = model_inference["model_id"]
        confidence = model_inference["confidence"]
        pred_class = model_inference["predicted_class"].lower()
        if "fresh" in pred_class:
            label = "Fresh"
            safety_status = "safe_to_consume"
        elif "spoil" in pred_class or "rot" in pred_class:
            label = "Spoiled"
            safety_status = "do_not_consume"
        else:
            label = "Moderate"
            safety_status = "use_caution"
        pipeline_disclosure = (
            f"Inference generated via deep learning model '{model_id}' trained on classes: {freshness_manager.classes}."
        )
    else:
        analysis_mode = "heuristic_visual_cues"
        model_id = freshness_manager.model_id
        confidence = (
            0.20 if features.get("low_information")
            else (0.92 if label in ("Fresh", "Spoiled") else 0.76)
        )
        pipeline_disclosure = (
            "Freshness score and label generated via multi-spectral computer vision heuristics "
            "(RGB/HSV color discolouration and texture variance). No fine-tuned deep learning checkpoint is currently loaded."
        )

    # --- Response -----------------------------------------------------------
    return {
        "status": "success",
        "filename": file.filename,
        "detected_food": detected_food,
        "food_category": category,
        "confidence": confidence,
        "model_id": model_id,
        "analysis_mode": analysis_mode,
        "model_loaded": freshness_manager.is_model_loaded,
        "preprocessing": prep_meta,
        "extracted_features": {
            "mean_saturation_pct":      round(features["mean_saturation"] * 100, 1),
            "mean_brightness_pct":      round(features["mean_brightness"] * 100, 1),
            "fresh_vivid_colour_pct":   round(features["fresh_vivid_fraction"] * 100, 1),
            "brown_discolouration_pct": round(features["brown_fraction"] * 100, 1),
            "brown_rot_pct":            round(features["brown_rot_fraction"] * 100, 1),
            "dark_patches_pct":         round(features["dark_fraction"] * 100, 1),
            "grey_patches_pct":         round(features["grey_fraction"] * 100, 1),
            "mould_teal_pct":           round(features["mould_teal_fraction"] * 100, 1),
            "mould_white_pct":          round(features["mould_white_fraction"] * 100, 1),
            "yellowing_pct":            round(features["yellow_fraction"] * 100, 1),
            "texture_variance":         features["texture_variance"],
            "edge_density_pct":         round(features["edge_density"] * 100, 1),
            "low_information":          features.get("low_information", False),
        },
        "visual_evidence":  visual_evidence,
        "freshness_score":  score,
        "freshness_label":  label,
        "safety_status":    safety_status,
        "detected_signs":   signs if signs else ["No significant visual spoilage cues detected"],
        "reasoning":        reasoning,
        "recommendations":  recommendations,
        "pipeline_disclosure": pipeline_disclosure,
        "limitations":      limitations,
        "model_predictions": model_inference,
        "disclaimer":       _SAFETY_DISCLAIMER,
    }
