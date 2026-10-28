from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.capabilities import router as capabilities_router
from app.api.v1.profile import router as profile_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.food import router as food_router
from app.api.v1.freshness import router as freshness_router
from app.api.v1.hygiene import router as hygiene_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.recipes import router as recipes_router
from app.api.v1.meal_plans import router as meal_plans_router
from app.api.v1.chat import router as chat_router
from app.api.v1.history import router as history_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(capabilities_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(profile_router)
api_v1_router.include_router(uploads_router)
api_v1_router.include_router(food_router)
api_v1_router.include_router(freshness_router)
api_v1_router.include_router(hygiene_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(recipes_router)
api_v1_router.include_router(meal_plans_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(history_router)

__all__ = ["api_v1_router"]
