from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import User, Recipe, FoodAnalysis
from app.schemas.dtos import RecipeGenerateRequest, RecipeOut
from app.api.deps import get_current_user
from app.services.recipe_service import generate_recipe_service

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.post("/generate", response_model=RecipeOut)
async def generate_recipe(
    req: RecipeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ingredients = list(req.ingredients)

    # Pull ingredients from previous food analyses if IDs supplied
    if req.from_food_analyses:
        for fa_id in req.from_food_analyses:
            fa = db.query(FoodAnalysis).filter(FoodAnalysis.id == fa_id).first()
            if fa and fa.food_name and fa.food_name not in ingredients:
                ingredients.append(fa.food_name)

    req_dict = req.model_dump()
    req_dict["ingredients"] = ingredients

    res = await generate_recipe_service(req_dict)

    record = Recipe(
        user_id=current_user.id,
        title=res.get("title", "Delicious Home Recipe"),
        description=res.get("description"),
        ingredients=res.get("ingredients", []),
        servings=res.get("servings", 2),
        prep_time_minutes=res.get("prep_time_minutes", 15),
        cook_time_minutes=res.get("cook_time_minutes", 20),
        instructions=res.get("instructions", []),
        substitutions=res.get("substitutions", []),
        storage_guidance=res.get("storage_guidance"),
        nutrition_estimates=res.get("nutrition_estimates", {}),
        allergen_warnings=res.get("allergen_warnings", []),
        is_saved=True,
        execution_mode=res.get("execution_mode", "demo"),
        provider=res.get("provider", "demo"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return RecipeOut(
        id=record.id,
        title=record.title,
        description=record.description,
        ingredients=record.ingredients or [],
        servings=record.servings,
        prep_time_minutes=record.prep_time_minutes,
        cook_time_minutes=record.cook_time_minutes,
        instructions=record.instructions or [],
        substitutions=record.substitutions or [],
        storage_guidance=record.storage_guidance,
        nutrition_estimates=record.nutrition_estimates or {},
        allergen_warnings=record.allergen_warnings or [],
        is_saved=record.is_saved,
        execution_mode=record.execution_mode,
        provider=record.provider,
        created_at=record.created_at,
    )

@router.get("", response_model=List[RecipeOut])
def list_recipes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recipes = db.query(Recipe).filter(Recipe.user_id == current_user.id).order_by(Recipe.created_at.desc()).all()
    return [
        RecipeOut(
            id=r.id,
            title=r.title,
            description=r.description,
            ingredients=r.ingredients or [],
            servings=r.servings,
            prep_time_minutes=r.prep_time_minutes,
            cook_time_minutes=r.cook_time_minutes,
            instructions=r.instructions or [],
            substitutions=r.substitutions or [],
            storage_guidance=r.storage_guidance,
            nutrition_estimates=r.nutrition_estimates or {},
            allergen_warnings=r.allergen_warnings or [],
            is_saved=r.is_saved,
            execution_mode=r.execution_mode,
            provider=r.provider,
            created_at=r.created_at,
        )
        for r in recipes
    ]

@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    r = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    if r.user_id != current_user.id and not current_user.is_demo:
        raise HTTPException(status_code=403, detail="Unauthorized access to recipe.")

    return RecipeOut(
        id=r.id,
        title=r.title,
        description=r.description,
        ingredients=r.ingredients or [],
        servings=r.servings,
        prep_time_minutes=r.prep_time_minutes,
        cook_time_minutes=r.cook_time_minutes,
        instructions=r.instructions or [],
        substitutions=r.substitutions or [],
        storage_guidance=r.storage_guidance,
        nutrition_estimates=r.nutrition_estimates or {},
        allergen_warnings=r.allergen_warnings or [],
        is_saved=r.is_saved,
        execution_mode=r.execution_mode,
        provider=r.provider,
        created_at=r.created_at,
    )
