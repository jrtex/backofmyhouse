from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
import httpx

from app.models.app_setting import AppSetting
from app.schemas.settings import AIProvider, SettingsResponse, AIConfigResponse
from app.utils.encryption import encrypt_value, decrypt_value


class SettingsService:
    """Service for managing application settings."""

    # Setting keys
    AI_PROVIDER_KEY = "ai_provider"
    OPENAI_API_KEY = "openai_api_key"
    ANTHROPIC_API_KEY = "anthropic_api_key"
    GEMINI_API_KEY = "gemini_api_key"

    API_KEY_SETTINGS = [OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY]

    @staticmethod
    def get_setting(db: Session, key: str) -> Optional[str]:
        """Get a setting value by key. Decrypts if encrypted."""
        setting = db.query(AppSetting).filter(AppSetting.key == key).first()
        if not setting or not setting.value:
            return None
        if setting.is_encrypted:
            return decrypt_value(setting.value)
        return setting.value

    @staticmethod
    def set_setting(db: Session, key: str, value: Optional[str], encrypt: bool = False) -> None:
        """Set a setting value. Optionally encrypt."""
        setting = db.query(AppSetting).filter(AppSetting.key == key).first()

        if value is None:
            # Delete setting if exists
            if setting:
                db.delete(setting)
                db.commit()
            return

        stored_value = encrypt_value(value) if encrypt else value

        if setting:
            setting.value = stored_value
            setting.is_encrypted = encrypt
            setting.updated_at = datetime.utcnow()
        else:
            setting = AppSetting(
                key=key,
                value=stored_value,
                is_encrypted=encrypt,
            )
            db.add(setting)

        db.commit()

    @staticmethod
    def get_all_settings(db: Session) -> SettingsResponse:
        """Get all settings with masked API keys."""
        ai_provider_val = SettingsService.get_setting(db, SettingsService.AI_PROVIDER_KEY)

        return SettingsResponse(
            ai_provider=AIProvider(ai_provider_val) if ai_provider_val else None,
            openai_api_key_configured=SettingsService.get_setting(db, SettingsService.OPENAI_API_KEY) is not None,
            anthropic_api_key_configured=SettingsService.get_setting(db, SettingsService.ANTHROPIC_API_KEY) is not None,
            gemini_api_key_configured=SettingsService.get_setting(db, SettingsService.GEMINI_API_KEY) is not None,
        )

    @staticmethod
    def get_ai_config(db: Session) -> Optional[AIConfigResponse]:
        """Get the active AI provider and its API key (for internal use)."""
        provider_val = SettingsService.get_setting(db, SettingsService.AI_PROVIDER_KEY)
        if not provider_val:
            return None

        provider = AIProvider(provider_val)
        key_map = {
            AIProvider.openai: SettingsService.OPENAI_API_KEY,
            AIProvider.anthropic: SettingsService.ANTHROPIC_API_KEY,
            AIProvider.gemini: SettingsService.GEMINI_API_KEY,
        }

        api_key = SettingsService.get_setting(db, key_map[provider])
        if not api_key:
            return None

        return AIConfigResponse(provider=provider, api_key=api_key)

    @staticmethod
    async def validate_openai_key(api_key: str) -> bool:
        """Validate OpenAI API key by listing models."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0,
                )
                return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    async def validate_anthropic_key(api_key: str) -> bool:
        """Validate Anthropic API key by sending a minimal request."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "Hi"}]
                    },
                    timeout=10.0,
                )
                # 200 = success, 400 = valid key but bad request format
                return response.status_code in (200, 400)
        except Exception:
            return False

    @staticmethod
    async def validate_gemini_key(api_key: str) -> bool:
        """Validate Gemini API key by listing models."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1/models?key={api_key}",
                    timeout=10.0,
                )
                return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    async def validate_api_key(provider: str, api_key: str) -> bool:
        """Validate an API key for a given provider."""
        validators = {
            "openai": SettingsService.validate_openai_key,
            "anthropic": SettingsService.validate_anthropic_key,
            "gemini": SettingsService.validate_gemini_key,
        }
        validator = validators.get(provider)
        if not validator:
            return False
        return await validator(api_key)
