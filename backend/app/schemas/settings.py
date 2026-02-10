import enum
from typing import Optional
from pydantic import BaseModel, Field


class AIProvider(str, enum.Enum):
    openai = "openai"
    anthropic = "anthropic"
    gemini = "gemini"


# Default model names for each provider
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"


class SettingsResponse(BaseModel):
    """Response for all application settings (API keys masked)."""
    ai_provider: Optional[AIProvider] = None
    openai_api_key_configured: bool = False
    anthropic_api_key_configured: bool = False
    gemini_api_key_configured: bool = False
    openai_model: str = DEFAULT_OPENAI_MODEL
    anthropic_model: str = DEFAULT_ANTHROPIC_MODEL
    gemini_model: str = DEFAULT_GEMINI_MODEL


class SettingsUpdate(BaseModel):
    """Request to update application settings."""
    ai_provider: Optional[AIProvider] = None
    openai_api_key: Optional[str] = Field(None, min_length=1)
    anthropic_api_key: Optional[str] = Field(None, min_length=1)
    gemini_api_key: Optional[str] = Field(None, min_length=1)
    openai_model: Optional[str] = Field(None, min_length=1)
    anthropic_model: Optional[str] = Field(None, min_length=1)
    gemini_model: Optional[str] = Field(None, min_length=1)


class AIConfigResponse(BaseModel):
    """Internal response for get_ai_config - contains decrypted API key."""
    provider: AIProvider
    api_key: str
    model: str
