import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.import_schemas import RecipeExtraction, TextImportRequest, UrlImportRequest
from app.services.ai.base import AIExtractionError, AINotConfiguredError, PDFNotSupportedError
from app.services.ai.factory import get_ai_provider
from app.services.ai_usage_service import AIUsageService
from app.services.url_scraper import UrlScraperService, UrlFetchError, UrlBlockedError
from app.services.schema_mapper import map_schema_org_to_extraction

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed MIME types for image and PDF import
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "application/pdf"}

# Maximum file size in bytes (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/image", response_model=RecipeExtraction)
async def import_from_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecipeExtraction:
    """Import a recipe from an image or PDF using AI extraction.

    Accepts JPEG, PNG, WebP, HEIC images and PDF files up to 10MB.
    Returns extracted recipe data for review before saving.
    """
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed types: JPEG, PNG, WebP, HEIC, PDF",
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

    input_type = "pdf" if file.content_type == "application/pdf" else "image"

    # Extract recipe from file (image or PDF)
    try:
        if file.content_type == "application/pdf":
            ai_result = await provider.extract_recipe_from_pdf(pdf_data=content)
        else:
            ai_result = await provider.extract_recipe_from_image(
                image_data=content,
                mime_type=file.content_type,
            )
        AIUsageService.log_usage(
            db=db,
            user_id=current_user.id,
            provider=ai_result.provider,
            model=ai_result.model,
            input_type=input_type,
            input_tokens=ai_result.input_tokens,
            output_tokens=ai_result.output_tokens,
            total_tokens=ai_result.total_tokens,
            success=True,
            duration_ms=ai_result.duration_ms,
        )
        logger.info(
            "Import complete",
            extra={"input_type": input_type, "title": ai_result.extraction.title, "user_id": str(current_user.id)},
        )
        return ai_result.extraction
    except PDFNotSupportedError as e:
        AIUsageService.log_usage(
            db=db,
            user_id=current_user.id,
            provider=provider.provider_name,
            model=provider.model,
            input_type=input_type,
            success=False,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except AIExtractionError as e:
        AIUsageService.log_usage(
            db=db,
            user_id=current_user.id,
            provider=provider.provider_name,
            model=provider.model,
            input_type=input_type,
            success=False,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract recipe from file: {str(e)}",
        )


@router.post("/url", response_model=RecipeExtraction)
async def import_from_url(
    request: UrlImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecipeExtraction:
    """Import a recipe from a URL.

    Attempts to extract recipe data from the URL. If the page contains
    schema.org Recipe structured data, it will be used directly.
    Otherwise, falls back to AI extraction from the page text.

    Returns extracted recipe data for review before saving.
    """
    # Fetch and parse URL
    scraper = UrlScraperService()
    try:
        url_content = await scraper.fetch_url_content(str(request.url))
    except UrlFetchError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not fetch URL: {str(e)}",
        )
    except UrlBlockedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Access blocked: {str(e)}",
        )

    # If schema.org Recipe data found, use it directly (no AI call)
    if url_content.schema_recipe:
        try:
            extraction = map_schema_org_to_extraction(url_content.schema_recipe)
            logger.info(
                "URL import using schema.org (no AI call)",
                extra={"user_id": str(current_user.id), "title": extraction.title},
            )
            return extraction
        except ValueError as e:
            # Invalid schema.org data, fall back to AI
            logger.warning("Schema.org parse failed, falling back to AI", extra={"error": str(e)})

    # Fall back to AI extraction from page text
    try:
        provider = get_ai_provider(db)
    except AINotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Please configure an AI provider in admin settings.",
        )

    try:
        ai_result = await provider.extract_recipe_from_text(url_content.text)
        AIUsageService.log_usage(
            db=db,
            user_id=current_user.id,
            provider=ai_result.provider,
            model=ai_result.model,
            input_type="url",
            input_tokens=ai_result.input_tokens,
            output_tokens=ai_result.output_tokens,
            total_tokens=ai_result.total_tokens,
            success=True,
            duration_ms=ai_result.duration_ms,
        )
        logger.info(
            "Import complete",
            extra={"input_type": "url", "title": ai_result.extraction.title, "user_id": str(current_user.id)},
        )
        return ai_result.extraction
    except AIExtractionError as e:
        AIUsageService.log_usage(
            db=db,
            user_id=current_user.id,
            provider=provider.provider_name,
            model=provider.model,
            input_type="url",
            success=False,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract recipe from URL: {str(e)}",
        )


@router.post("/text", response_model=RecipeExtraction)
async def import_from_text(
    request: TextImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecipeExtraction:
    """Import a recipe from raw text using AI extraction.

    Accepts plain text containing recipe information (ingredients, instructions, etc.)
    and uses AI to parse it into structured recipe data.

    Returns extracted recipe data for review before saving.
    """
    try:
        provider = get_ai_provider(db)
    except AINotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Please configure an AI provider in admin settings.",
        )

    try:
        ai_result = await provider.extract_recipe_from_text(request.text)
        AIUsageService.log_usage(
            db=db,
            user_id=current_user.id,
            provider=ai_result.provider,
            model=ai_result.model,
            input_type="text",
            input_tokens=ai_result.input_tokens,
            output_tokens=ai_result.output_tokens,
            total_tokens=ai_result.total_tokens,
            success=True,
            duration_ms=ai_result.duration_ms,
        )
        logger.info(
            "Import complete",
            extra={"input_type": "text", "title": ai_result.extraction.title, "user_id": str(current_user.id)},
        )
        return ai_result.extraction
    except AIExtractionError as e:
        AIUsageService.log_usage(
            db=db,
            user_id=current_user.id,
            provider=provider.provider_name,
            model=provider.model,
            input_type="text",
            success=False,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract recipe from text: {str(e)}",
        )
