from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl

from app.schemas.recipe import Ingredient, Instruction


class UrlImportRequest(BaseModel):
    """Request schema for importing a recipe from a URL."""

    url: HttpUrl


class TextImportRequest(BaseModel):
    """Request schema for importing a recipe from raw text."""

    text: str = Field(..., min_length=10, max_length=50000)


class RecipeExtraction(BaseModel):
    """Schema for AI-extracted recipe data.

    This schema represents the structured output from AI providers
    when extracting recipe information from images or text.
    """

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    ingredients: List[Ingredient] = Field(default_factory=list)
    instructions: List[Instruction] = Field(default_factory=list)
    prep_time_minutes: Optional[int] = Field(None, ge=0)
    cook_time_minutes: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None
    special_equipment: Optional[List[str]] = None
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence score (0-1)")
    warnings: List[str] = Field(default_factory=list, description="Any issues encountered during extraction")
