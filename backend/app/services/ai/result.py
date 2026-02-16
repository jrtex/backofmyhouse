from dataclasses import dataclass
from typing import Optional

from app.schemas.import_schemas import RecipeExtraction


@dataclass
class AIExtractionResult:
    extraction: RecipeExtraction
    provider: str
    model: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    duration_ms: Optional[int] = None
