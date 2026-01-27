import enum
from typing import Optional
from pydantic import BaseModel, Field


class AIProvider(str, enum.Enum):
    openai = "openai"
    anthropic = "anthropic"
    gemini = "gemini"


class SettingsResponse(BaseModel):
    """Response for all application settings (API keys masked)."""
    ai_provider: Optional[AIProvider] = None
    openai_api_key_configured: bool = False
    anthropic_api_key_configured: bool = False
    gemini_api_key_configured: bool = False


class SettingsUpdate(BaseModel):
    """Request to update application settings."""
    ai_provider: Optional[AIProvider] = None
    openai_api_key: Optional[str] = Field(None, min_length=1)
    anthropic_api_key: Optional[str] = Field(None, min_length=1)
    gemini_api_key: Optional[str] = Field(None, min_length=1)


class AIConfigResponse(BaseModel):
    """Internal response for get_ai_config - contains decrypted API key."""
    provider: AIProvider
    api_key: str
