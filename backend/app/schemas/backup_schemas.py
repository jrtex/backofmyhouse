from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel


class BackupIngredient(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None


class BackupInstruction(BaseModel):
    step_number: int
    text: str


class BackupRecipe(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: List[BackupIngredient]
    instructions: List[BackupInstruction]
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    notes: Optional[str] = None
    complexity: Optional[str] = None
    special_equipment: Optional[List[str]] = None
    source_author: Optional[str] = None
    source_url: Optional[str] = None
    category_name: Optional[str] = None
    tag_names: List[str] = []
    original_author: str
    created_at: datetime


class BackupMetadata(BaseModel):
    format_version: str = "1.0"
    exported_at: datetime
    recipe_count: int


class BackupExport(BaseModel):
    metadata: BackupMetadata
    recipes: List[BackupRecipe]


class ConflictStrategy(str, Enum):
    skip = "skip"
    replace = "replace"
    rename = "rename"


class ImportResult(BaseModel):
    total_in_file: int
    total_selected: int
    created: int
    skipped: int
    replaced: int
    errors: int
    categories_created: int
    tags_created: int
    error_details: List[dict]
