from sqlalchemy.orm import Session

from app.schemas.settings import AIProvider as AIProviderEnum
from app.services.ai.base import AIProvider, AINotConfiguredError
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.anthropic_provider import AnthropicProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.settings import SettingsService


def get_ai_provider(db: Session) -> AIProvider:
    """Get the configured AI provider instance.

    Reads the AI configuration from settings and returns an initialized
    provider instance ready for recipe extraction.

    Args:
        db: Database session for reading settings.

    Returns:
        An initialized AIProvider instance.

    Raises:
        AINotConfiguredError: If no AI provider is configured or the
            selected provider's API key is not set.
    """
    config = SettingsService.get_ai_config(db)

    if not config:
        raise AINotConfiguredError(
            "No AI provider configured. Please configure an AI provider "
            "and API key in the admin settings."
        )

    provider_classes = {
        AIProviderEnum.openai: OpenAIProvider,
        AIProviderEnum.anthropic: AnthropicProvider,
        AIProviderEnum.gemini: GeminiProvider,
    }

    provider_class = provider_classes.get(config.provider)
    if not provider_class:
        raise AINotConfiguredError(f"Unknown AI provider: {config.provider}")

    return provider_class(api_key=config.api_key, model=config.model)
