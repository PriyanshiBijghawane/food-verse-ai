import base64
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import httpx
from app.core.config import settings
from app.providers.base import BaseAIProvider

logger = logging.getLogger("food_verse_ai.gemini_provider")

class GeminiAIProvider(BaseAIProvider):
    """
    Real Multimodal AI Provider using Google Gemini API.
    Supports structured JSON vision inference, freshness evaluation, kitchen hygiene auditing,
    recipe generation, and meal planning.
    """
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.AI_API_KEY
        self.model = model or settings.AI_MODEL
        if not self.model or self.model.strip() == "":
            self.model = "gemini-1.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def execution_mode(self) -> str:
        return "real"

    async def _call_gemini(self, contents: List[Dict[str, Any]], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured on the server. Please switch to Demo Mode or configure credentials.")

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            }
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        async with httpx.AsyncClient(timeout=35.0) as client:
            for attempt in range(2):
                try:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            raise ValueError("Gemini returned empty candidates")
                        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
                        return json.loads(raw_text)
                    elif response.status_code in (429, 503) and attempt == 0:
                        logger.warning("Gemini rate limit or temporary server error, retrying...")
                        continue
                    else:
                        error_detail = response.text[:200]
                        logger.error("Gemini API error status %s: %s", response.status_code, error_detail)
                        raise ValueError(f"Gemini API returned status {response.status_code}: {error_detail}")
                except (httpx.TimeoutException, httpx.RequestError) as exc:
                    if attempt == 0:
                        continue
                    raise ValueError(f"Network error communicating with Gemini provider: {exc}")

        raise ValueError("Failed to obtain response from Gemini provider after retries.")

    async def analyze_food_image(
        self, image_bytes: bytes, description: Optional[str] = None
    ) -> Dict[str, Any]:
        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "You are a nutritional computer vision specialist. Identify visible foods, estimate portion size in grams, "
            "and compute reference nutritional values. Respond in valid JSON with schema:\n"
            "{\n"
            '  "food_name": "string",\n'
            '  "candidate_foods": [{"label": "string", "confidence": float, "region": "string"}],\n'
            '  "confidence": float,\n'
            '  "portion_grams": float,\n'
            '  "portion_unit": "grams",\n'
            '  "calories": float,\n'
            '  "protein_g": float,\n'
            '  "carbs_g": float,\n'
            '  "fat_g": float,\n'
            '  "fiber_g": float,\n'
            '  "sodium_mg": float,\n'
            '  "nutritional_score": float,\n'
            '  "score_explanation": "string",\n'
            '  "uncertainty_notes": "string",\n'
            '  "detected_items": [{"name": "string", "portion_grams": float, "calories": float, "protein_g": float}]\n'
            "}"
        )
        if description:
            prompt += f"\nUser supplied food context: {description}"

        contents = [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}},
                {"text": prompt}
            ]
        }]
        result = await self._call_gemini(contents)
        result["provenance"] = "gemini_multimodal_estimate"
        result["execution_mode"] = "real"
        result["provider"] = "gemini"
        result["model_id"] = self.model
        return result

    async def assess_visible_freshness(
        self, image_bytes: bytes, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "Assess visible signs of food freshness and surface spoilage. "
            "CRITICAL SAFETY RULE: You cannot determine microbiological safety or detect pathogens from imagery. "
            "Categorize into exactly one of: 'no_obvious_visible_spoilage', 'possible_visible_spoilage', "
            "'visible_spoilage_observed', 'insufficient_information'.\n"
            "Return JSON matching:\n"
            "{\n"
            '  "food_type": "string",\n'
            '  "spoilage_category": "string",\n'
            '  "category_label": "string",\n'
            '  "visual_observations": ["string"],\n'
            '  "limitations": "string",\n'
            '  "conservative_next_steps": ["string"]\n'
            "}"
        )
        prompt += f"\nStorage context: {json.dumps(context)}"

        contents = [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}},
                {"text": prompt}
            ]
        }]
        result = await self._call_gemini(contents)
        result["storage_context"] = context
        result["execution_mode"] = "real"
        result["provider"] = "gemini"
        result["model_id"] = self.model
        return result

    async def analyze_kitchen_image(
        self, image_bytes: bytes, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "Perform an observational sanitation audit of this kitchen area. "
            "Evaluate observable surfaces, visible waste, storage separation, protective wear. "
            "DO NOT claim official health department certification or legal compliance.\n"
            "Return JSON:\n"
            "{\n"
            '  "media_type": "image",\n'
            '  "checklist_score": float,\n'
            '  "score_formula": "string",\n'
            '  "findings": [{"area": "string", "observation": "string", "severity": "info"|"minor"|"moderate"|"critical", "corrective_action": "string"}],\n'
            '  "unobservable_items": ["string"]\n'
            "}"
        )
        contents = [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}},
                {"text": prompt}
            ]
        }]
        result = await self._call_gemini(contents)
        result["execution_mode"] = "real"
        result["provider"] = "gemini"
        result["model_id"] = self.model
        return result

    async def analyze_video_frames(
        self, frames: List[Tuple[float, bytes]]
    ) -> Dict[str, Any]:
        parts = []
        for timestamp, frame_bytes in frames[:6]:  # sample up to 6 frames for multimodal prompt
            b64_img = base64.b64encode(frame_bytes).decode("utf-8")
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64_img}})
            parts.append({"text": f"Frame sampled at {timestamp:.1f}s"})

        prompt = (
            "Analyze these sampled video frames for kitchen sanitation observations. "
            "Return JSON:\n"
            "{\n"
            '  "media_type": "video",\n'
            '  "frames_analyzed": int,\n'
            '  "checklist_score": float,\n'
            '  "score_formula": "string",\n'
            '  "findings": [{"area": "string", "observation": "string", "severity": "info"|"minor"|"moderate"|"critical", "corrective_action": "string", "timestamp_seconds": float}],\n'
            '  "unobservable_items": ["string"]\n'
            "}"
        )
        parts.append({"text": prompt})

        contents = [{"parts": parts}]
        result = await self._call_gemini(contents)
        result["frames_analyzed"] = len(frames)
        result["execution_mode"] = "real"
        result["provider"] = "gemini"
        result["model_id"] = self.model
        return result

    async def generate_recipe(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = (
            "Generate a detailed, culinary-sound recipe based on the input request. "
            "Include exact ingredients with quantities, ordered steps with optional timers, substitutions, storage, and nutrition. "
            "CRITICAL: Include allergen warnings if any top allergens are present.\n"
            "Return JSON matching:\n"
            "{\n"
            '  "title": "string",\n'
            '  "description": "string",\n'
            '  "ingredients": [{"name": "string", "quantity": "string", "unit": "string", "optional": false}],\n'
            '  "servings": int,\n'
            '  "prep_time_minutes": int,\n'
            '  "cook_time_minutes": int,\n'
            '  "instructions": [{"step": int, "instruction": "string", "timer_minutes": int|null}],\n'
            '  "substitutions": [{"original": "string", "alternative": "string"}],\n'
            '  "storage_guidance": "string",\n'
            '  "nutrition_estimates": {"calories_per_serving": int, "protein_g": float, "carbs_g": float, "fat_g": float, "fiber_g": float, "sodium_mg": int},\n'
            '  "allergen_warnings": ["string"]\n'
            "}"
        )
        prompt += f"\nRequest: {json.dumps(request_data)}"
        contents = [{"parts": [{"text": prompt}]}]
        result = await self._call_gemini(contents)
        result["execution_mode"] = "real"
        result["provider"] = "gemini"
        return result

    async def generate_meal_plan(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = (
            "Generate a structured daily or 7-day personalized meal plan. "
            "Strictly avoid any ingredients in the allergens or exclusions list.\n"
            "Return JSON matching:\n"
            "{\n"
            '  "title": "string",\n'
            '  "plan_type": "string",\n'
            '  "daily_target_calories": float,\n'
            '  "diet_type": "string",\n'
            '  "total_estimated_calories": float,\n'
            '  "total_protein_g": float,\n'
            '  "total_carbs_g": float,\n'
            '  "total_fat_g": float,\n'
            '  "allergen_notes": ["string"],\n'
            '  "items": [\n'
            '    {"day_number": int, "meal_type": "breakfast"|"lunch"|"dinner"|"snack", "meal_name": "string", "description": "string", "servings": int, "ingredients": ["string"], "calories": float, "protein_g": float, "carbs_g": float, "fat_g": float}\n'
            '  ]\n'
            "}"
        )
        prompt += f"\nRequest: {json.dumps(request_data)}"
        contents = [{"parts": [{"text": prompt}]}]
        result = await self._call_gemini(contents)
        result["execution_mode"] = "real"
        return result

    async def transcribe_audio(
        self, audio_bytes: bytes
    ) -> Dict[str, Any]:
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        prompt = (
            "Transcribe this audio recording into text. Return JSON:\n"
            '{"transcript": "string", "confidence": float, "audio_duration_seconds": float}'
        )
        contents = [{
            "parts": [
                {"inline_data": {"mime_type": "audio/mp3", "data": b64_audio}},
                {"text": prompt}
            ]
        }]
        result = await self._call_gemini(contents)
        return result
