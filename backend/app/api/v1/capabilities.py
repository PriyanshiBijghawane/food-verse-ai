from fastapi import APIRouter
from app.core.config import settings
from app.schemas.dtos import CapabilitiesResponse

router = APIRouter(tags=["capabilities"])

@router.get("/capabilities", response_model=CapabilitiesResponse)
def get_capabilities():
    has_key = bool(settings.AI_API_KEY and len(settings.AI_API_KEY.strip()) > 5)
    return CapabilitiesResponse(
        app_env=settings.APP_ENV,
        ai_mode=settings.AI_MODE,
        ai_provider=settings.AI_PROVIDER,
        ai_model=settings.AI_MODEL,
        has_api_key=has_key,
        supported_features={
            "food_recognition": True,
            "nutrition_estimation": True,
            "freshness_assessment": True,
            "kitchen_hygiene_image": True,
            "kitchen_hygiene_video": True,
            "smart_cooking_assistant": True,
            "personalized_meal_planner": True,
            "audio_transcription": True,
            "user_data_persistence": True,
        },
        disclaimers={
            "visual_limits": "Visual inspection cannot establish microbiological food safety or identify invisible pathogens.",
            "nutrition": "Nutrition data are estimates from reference models, not direct chemical laboratory assays.",
            "hygiene": "Hygiene scores are observational checklist assessments and do not constitute legal regulatory certification.",
            "medical": "Meal plans are informational lifestyle guides, not clinical nutrition therapy.",
        }
    )
