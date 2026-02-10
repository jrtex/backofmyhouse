from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.services.settings import SettingsService

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SettingsResponse:
    """Get all application settings (admin only).

    API keys are masked - only shows whether they are configured.
    """
    return SettingsService.get_all_settings(db)


@router.put("", response_model=SettingsResponse)
async def update_settings(
    settings_data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SettingsResponse:
    """Update application settings (admin only).

    API keys are validated before being saved.
    """
    # Update AI provider if provided
    if settings_data.ai_provider is not None:
        SettingsService.set_setting(
            db, SettingsService.AI_PROVIDER_KEY, settings_data.ai_provider.value
        )

    # Validate and update API keys
    api_key_updates = [
        ("openai", settings_data.openai_api_key, SettingsService.OPENAI_API_KEY),
        ("anthropic", settings_data.anthropic_api_key, SettingsService.ANTHROPIC_API_KEY),
        ("gemini", settings_data.gemini_api_key, SettingsService.GEMINI_API_KEY),
    ]

    for provider, api_key, setting_key in api_key_updates:
        if api_key is not None:
            # Validate the API key before saving
            is_valid = await SettingsService.validate_api_key(provider, api_key)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid {provider.upper()} API key",
                )
            SettingsService.set_setting(db, setting_key, api_key, encrypt=True)

    # Update model names (no validation needed)
    model_updates = [
        (settings_data.openai_model, SettingsService.OPENAI_MODEL_KEY),
        (settings_data.anthropic_model, SettingsService.ANTHROPIC_MODEL_KEY),
        (settings_data.gemini_model, SettingsService.GEMINI_MODEL_KEY),
    ]

    for model_name, setting_key in model_updates:
        if model_name is not None:
            SettingsService.set_setting(db, setting_key, model_name)

    return SettingsService.get_all_settings(db)
