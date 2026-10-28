from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import User, MealPlan, MealPlanItem
from app.schemas.dtos import (
    MealPlanGenerateRequest,
    MealReplaceRequest,
    MealPlanOut,
    MealItemOut,
    ShoppingListOut,
)
from app.api.deps import get_current_user
from app.services.meal_planner_service import (
    generate_plan_service,
    generate_replacement_meal,
    build_consolidated_shopping_list,
    filter_conflicting_meals,
)

router = APIRouter(prefix="/meal-plans", tags=["meal_plans"])

@router.post("", response_model=MealPlanOut)
async def create_meal_plan(
    req: MealPlanGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan_dict = await generate_plan_service(req.model_dump())

    # Strict allergen and exclusion validation
    raw_items = plan_dict.get("items", [])
    safe_items = filter_conflicting_meals(raw_items, req.allergies or [], req.disliked_ingredients or [])

    # If any items were filtered out, replace them with safe alternates
    final_items = []
    for item in raw_items:
        if item in safe_items:
            final_items.append(item)
        else:
            rep = generate_replacement_meal(
                item["day_number"],
                item["meal_type"],
                target_cals=item.get("calories", 500.0),
                diet_type=req.diet_type or "balanced",
                exclude_ingredients=(req.allergies or []) + (req.disliked_ingredients or [])
            )
            final_items.append(rep)

    # Persist meal plan
    plan_record = MealPlan(
        user_id=current_user.id,
        title=plan_dict.get("title", f"Personalized {req.plan_type.title()} Plan"),
        plan_type=req.plan_type,
        daily_target_calories=req.target_calories or 2000.0,
        diet_type=req.diet_type or "balanced",
        total_estimated_calories=sum(i.get("calories") or 0 for i in final_items),
        total_protein_g=sum(i.get("protein_g") or 0 for i in final_items),
        total_carbs_g=sum(i.get("carbs_g") or 0 for i in final_items),
        total_fat_g=sum(i.get("fat_g") or 0 for i in final_items),
        allergen_notes=plan_dict.get("allergen_notes", []),
        execution_mode=plan_dict.get("execution_mode", "demo"),
    )
    db.add(plan_record)
    db.commit()
    db.refresh(plan_record)

    # Persist meal plan items
    persisted_items = []
    for item in final_items:
        m_item = MealPlanItem(
            meal_plan_id=plan_record.id,
            day_number=item.get("day_number", 1),
            meal_type=item.get("meal_type", "lunch"),
            meal_name=item.get("meal_name", "Wholesome Plate"),
            description=item.get("description"),
            servings=item.get("servings", 1),
            ingredients=item.get("ingredients", []),
            calories=item.get("calories"),
            protein_g=item.get("protein_g"),
            carbs_g=item.get("carbs_g"),
            fat_g=item.get("fat_g"),
        )
        db.add(m_item)
        persisted_items.append(m_item)

    db.commit()

    return MealPlanOut(
        id=plan_record.id,
        title=plan_record.title,
        plan_type=plan_record.plan_type,
        daily_target_calories=plan_record.daily_target_calories,
        diet_type=plan_record.diet_type,
        total_estimated_calories=plan_record.total_estimated_calories,
        total_protein_g=plan_record.total_protein_g,
        total_carbs_g=plan_record.total_carbs_g,
        total_fat_g=plan_record.total_fat_g,
        allergen_notes=plan_record.allergen_notes or [],
        execution_mode=plan_record.execution_mode,
        created_at=plan_record.created_at,
        items=[
            MealItemOut(
                id=pi.id,
                day_number=pi.day_number,
                meal_type=pi.meal_type,
                meal_name=pi.meal_name,
                description=pi.description,
                servings=pi.servings,
                ingredients=pi.ingredients or [],
                calories=pi.calories,
                protein_g=pi.protein_g,
                carbs_g=pi.carbs_g,
                fat_g=pi.fat_g,
            )
            for pi in persisted_items
        ],
    )

@router.get("", response_model=List[MealPlanOut])
def list_meal_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plans = db.query(MealPlan).filter(MealPlan.user_id == current_user.id).order_by(MealPlan.created_at.desc()).all()
    results = []
    for p in plans:
        items = db.query(MealPlanItem).filter(MealPlanItem.meal_plan_id == p.id).order_by(MealPlanItem.day_number.asc()).all()
        results.append(
            MealPlanOut(
                id=p.id,
                title=p.title,
                plan_type=p.plan_type,
                daily_target_calories=p.daily_target_calories,
                diet_type=p.diet_type,
                total_estimated_calories=p.total_estimated_calories,
                total_protein_g=p.total_protein_g,
                total_carbs_g=p.total_carbs_g,
                total_fat_g=p.total_fat_g,
                allergen_notes=p.allergen_notes or [],
                execution_mode=p.execution_mode,
                created_at=p.created_at,
                items=[
                    MealItemOut(
                        id=it.id,
                        day_number=it.day_number,
                        meal_type=it.meal_type,
                        meal_name=it.meal_name,
                        description=it.description,
                        servings=it.servings,
                        ingredients=it.ingredients or [],
                        calories=it.calories,
                        protein_g=it.protein_g,
                        carbs_g=it.carbs_g,
                        fat_g=it.fat_g,
                    )
                    for it in items
                ]
            )
        )
    return results

@router.get("/{plan_id}", response_model=MealPlanOut)
def get_meal_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Meal plan not found.")
    if p.user_id != current_user.id and not current_user.is_demo:
        raise HTTPException(status_code=403, detail="Unauthorized access to meal plan.")

    items = db.query(MealPlanItem).filter(MealPlanItem.meal_plan_id == p.id).order_by(MealPlanItem.day_number.asc()).all()
    return MealPlanOut(
        id=p.id,
        title=p.title,
        plan_type=p.plan_type,
        daily_target_calories=p.daily_target_calories,
        diet_type=p.diet_type,
        total_estimated_calories=p.total_estimated_calories,
        total_protein_g=p.total_protein_g,
        total_carbs_g=p.total_carbs_g,
        total_fat_g=p.total_fat_g,
        allergen_notes=p.allergen_notes or [],
        execution_mode=p.execution_mode,
        created_at=p.created_at,
        items=[
            MealItemOut(
                id=it.id,
                day_number=it.day_number,
                meal_type=it.meal_type,
                meal_name=it.meal_name,
                description=it.description,
                servings=it.servings,
                ingredients=it.ingredients or [],
                calories=it.calories,
                protein_g=it.protein_g,
                carbs_g=it.carbs_g,
                fat_g=it.fat_g,
            )
            for it in items
        ]
    )

@router.post("/{plan_id}/replace-meal", response_model=MealPlanOut)
def replace_single_meal(
    plan_id: str,
    req: MealReplaceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found.")
    if plan.user_id != current_user.id and not current_user.is_demo:
        raise HTTPException(status_code=403, detail="Unauthorized access to meal plan.")

    existing_item = db.query(MealPlanItem).filter(
        MealPlanItem.meal_plan_id == plan_id,
        MealPlanItem.day_number == req.day_number,
        MealPlanItem.meal_type == req.meal_type
    ).first()

    target_cal = existing_item.calories if (existing_item and existing_item.calories) else 450.0

    new_meal = generate_replacement_meal(
        day_number=req.day_number,
        meal_type=req.meal_type,
        target_cals=target_cal,
        diet_type=plan.diet_type,
        exclude_ingredients=req.exclude_ingredients or []
    )

    if existing_item:
        existing_item.meal_name = new_meal["meal_name"]
        existing_item.description = new_meal["description"]
        existing_item.ingredients = new_meal["ingredients"]
        existing_item.calories = new_meal["calories"]
        existing_item.protein_g = new_meal["protein_g"]
        existing_item.carbs_g = new_meal["carbs_g"]
        existing_item.fat_g = new_meal["fat_g"]
        db.add(existing_item)
    else:
        new_record = MealPlanItem(
            meal_plan_id=plan_id,
            day_number=req.day_number,
            meal_type=req.meal_type,
            meal_name=new_meal["meal_name"],
            description=new_meal["description"],
            servings=1,
            ingredients=new_meal["ingredients"],
            calories=new_meal["calories"],
            protein_g=new_meal["protein_g"],
            carbs_g=new_meal["carbs_g"],
            fat_g=new_meal["fat_g"],
        )
        db.add(new_record)

    db.commit()

    # Recalculate plan totals
    all_items = db.query(MealPlanItem).filter(MealPlanItem.meal_plan_id == plan_id).all()
    plan.total_estimated_calories = sum(i.calories or 0 for i in all_items)
    plan.total_protein_g = sum(i.protein_g or 0 for i in all_items)
    plan.total_carbs_g = sum(i.carbs_g or 0 for i in all_items)
    plan.total_fat_g = sum(i.fat_g or 0 for i in all_items)
    db.commit()
    db.refresh(plan)

    return get_meal_plan(plan_id, current_user, db)

@router.get("/{plan_id}/shopping-list", response_model=ShoppingListOut)
def get_shopping_list(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found.")
    if plan.user_id != current_user.id and not current_user.is_demo:
        raise HTTPException(status_code=403, detail="Unauthorized access to meal plan.")

    items = db.query(MealPlanItem).filter(MealPlanItem.meal_plan_id == plan_id).all()
    result = build_consolidated_shopping_list(plan.title, plan.id, items)
    return ShoppingListOut(**result)
