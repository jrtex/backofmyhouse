from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.category import CategoryResponse
from app.schemas.tag import TagResponse
from app.schemas.user import UserResponse


class RecipeComplexityEnum(str, Enum):
    very_easy = "very_easy"
    easy = "easy"
    medium = "medium"
    hard = "hard"
    very_hard = "very_hard"


class Ingredient(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None


class Instruction(BaseModel):
    step_number: int
    text: str


class RecipeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    ingredients: List[Ingredient] = Field(default_factory=list)
    instructions: List[Instruction] = Field(default_factory=list)
    prep_time_minutes: Optional[int] = Field(None, ge=0)
    cook_time_minutes: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None
    category_id: Optional[UUID] = None
    tag_ids: List[UUID] = Field(default_factory=list)
    complexity: Optional[RecipeComplexityEnum] = None
    special_equipment: Optional[List[str]] = None
    source_author: Optional[str] = Field(None, max_length=255)
    source_url: Optional[str] = Field(None, max_length=2048)


class RecipeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    ingredients: Optional[List[Ingredient]] = None
    instructions: Optional[List[Instruction]] = None
    prep_time_minutes: Optional[int] = Field(None, ge=0)
    cook_time_minutes: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None
    category_id: Optional[UUID] = None
    tag_ids: Optional[List[UUID]] = None
    complexity: Optional[RecipeComplexityEnum] = None
    special_equipment: Optional[List[str]] = None
    source_author: Optional[str] = Field(None, max_length=255)
    source_url: Optional[str] = Field(None, max_length=2048)


class RecipeResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    ingredients: List[Ingredient]
    instructions: List[Instruction]
    prep_time_minutes: Optional[int]
    cook_time_minutes: Optional[int]
    servings: Optional[int]
    notes: Optional[str]
    complexity: Optional[RecipeComplexityEnum]
    special_equipment: Optional[List[str]]
    source_author: Optional[str]
    source_url: Optional[str]
    category: Optional[CategoryResponse]
    user: UserResponse
    tags: List[TagResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecipeListResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    prep_time_minutes: Optional[int]
    cook_time_minutes: Optional[int]
    servings: Optional[int]
    category: Optional[CategoryResponse]
    tags: List[TagResponse]
    user: UserResponse
    created_at: datetime

    class Config:
        from_attributes = True
