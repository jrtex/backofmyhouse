from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.import_schemas import RecipeExtraction
from app.services.ai.base import AIExtractionError, AINotConfiguredError
from app.services.ai.factory import get_ai_provider

router = APIRouter()

# Allowed image MIME types
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}

# Maximum file size in bytes (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/image", response_model=RecipeExtraction)
async def import_from_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecipeExtraction:
    """Import a recipe from an image using AI extraction.

    Accepts JPEG, PNG, WebP, and HEIC images up to 10MB.
    Returns extracted recipe data for review before saving.
    """
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed types: JPEG, PNG, WebP, HEIC",
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size: 10MB",
        )

    # Get AI provider
    try:
        provider = get_ai_provider(db)
    except AINotConfiguredError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Please configure an AI provider in admin settings.",
        )

    # Extract recipe from image
    try:
        result = await provider.extract_recipe_from_image(
            image_data=content,
            mime_type=file.content_type,
        )
    except AIExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract recipe from image: {str(e)}",
        )

    return result
