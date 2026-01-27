from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.recipe import Recipe
from app.models.category import Category
from app.models.tag import Tag
from app.models.user import User, UserRole
from app.schemas.recipe import RecipeCreate, RecipeUpdate, RecipeResponse, RecipeListResponse

router = APIRouter()


@router.get("", response_model=List[RecipeListResponse])
async def list_recipes(
    category_id: Optional[UUID] = Query(None),
    tag_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    user_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Recipe).options(
        joinedload(Recipe.category),
        joinedload(Recipe.tags),
        joinedload(Recipe.user),
    )

    if category_id:
        query = query.filter(Recipe.category_id == category_id)

    if tag_id:
        query = query.filter(Recipe.tags.any(Tag.id == tag_id))

    if search:
        search_term = f"%{search}%"
        query = query.filter(Recipe.title.ilike(search_term))

    if user_id:
        query = query.filter(Recipe.user_id == user_id)

    recipes = query.order_by(Recipe.created_at.desc()).offset(skip).limit(limit).all()
    return recipes


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recipe = db.query(Recipe).options(
        joinedload(Recipe.category),
        joinedload(Recipe.tags),
        joinedload(Recipe.user),
    ).filter(Recipe.id == recipe_id).first()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )
    return recipe


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if recipe_data.category_id:
        category = db.query(Category).filter(Category.id == recipe_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found",
            )

    tags = []
    if recipe_data.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(recipe_data.tag_ids)).all()
        if len(tags) != len(recipe_data.tag_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more tags not found",
            )

    recipe = Recipe(
        title=recipe_data.title,
        description=recipe_data.description,
        ingredients=[ing.model_dump() for ing in recipe_data.ingredients],
        instructions=[inst.model_dump() for inst in recipe_data.instructions],
        prep_time_minutes=recipe_data.prep_time_minutes,
        cook_time_minutes=recipe_data.cook_time_minutes,
        servings=recipe_data.servings,
        notes=recipe_data.notes,
        complexity=recipe_data.complexity,
        special_equipment=recipe_data.special_equipment,
        source_author=recipe_data.source_author,
        source_url=recipe_data.source_url,
        category_id=recipe_data.category_id,
        user_id=current_user.id,
    )
    recipe.tags = tags

    db.add(recipe)
    db.commit()
    db.refresh(recipe)

    return db.query(Recipe).options(
        joinedload(Recipe.category),
        joinedload(Recipe.tags),
        joinedload(Recipe.user),
    ).filter(Recipe.id == recipe.id).first()


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: UUID,
    recipe_data: RecipeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    if recipe.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this recipe",
        )

    if recipe_data.title is not None:
        recipe.title = recipe_data.title
    if recipe_data.description is not None:
        recipe.description = recipe_data.description
    if recipe_data.ingredients is not None:
        recipe.ingredients = [ing.model_dump() for ing in recipe_data.ingredients]
    if recipe_data.instructions is not None:
        recipe.instructions = [inst.model_dump() for inst in recipe_data.instructions]
    if recipe_data.prep_time_minutes is not None:
        recipe.prep_time_minutes = recipe_data.prep_time_minutes
    if recipe_data.cook_time_minutes is not None:
        recipe.cook_time_minutes = recipe_data.cook_time_minutes
    if recipe_data.servings is not None:
        recipe.servings = recipe_data.servings
    if recipe_data.notes is not None:
        recipe.notes = recipe_data.notes
    if recipe_data.complexity is not None:
        recipe.complexity = recipe_data.complexity
    if recipe_data.special_equipment is not None:
        recipe.special_equipment = recipe_data.special_equipment
    if recipe_data.source_author is not None:
        recipe.source_author = recipe_data.source_author
    if recipe_data.source_url is not None:
        recipe.source_url = recipe_data.source_url

    if recipe_data.category_id is not None:
        if recipe_data.category_id:
            category = db.query(Category).filter(Category.id == recipe_data.category_id).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category not found",
                )
        recipe.category_id = recipe_data.category_id

    if recipe_data.tag_ids is not None:
        if recipe_data.tag_ids:
            tags = db.query(Tag).filter(Tag.id.in_(recipe_data.tag_ids)).all()
            if len(tags) != len(recipe_data.tag_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more tags not found",
                )
            recipe.tags = tags
        else:
            recipe.tags = []

    db.commit()
    db.refresh(recipe)

    return db.query(Recipe).options(
        joinedload(Recipe.category),
        joinedload(Recipe.tags),
        joinedload(Recipe.user),
    ).filter(Recipe.id == recipe.id).first()


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    if recipe.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this recipe",
        )

    db.delete(recipe)
    db.commit()
    return None
