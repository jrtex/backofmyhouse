import pytest
from unittest.mock import MagicMock, patch

from app.schemas.settings import AIProvider as AIProviderEnum, AIConfigResponse
from app.services.ai import (
    get_ai_provider,
    AINotConfiguredError,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
)


class TestGetAIProvider:
    """Tests for the get_ai_provider factory function."""

    def test_returns_openai_provider_when_configured(self):
        """Should return OpenAI provider when OpenAI is configured."""
        mock_db = MagicMock()
        config = AIConfigResponse(
            provider=AIProviderEnum.openai,
            api_key="sk-test-key",
        )

        with patch(
            "app.services.ai.factory.SettingsService.get_ai_config",
            return_value=config,
        ):
            provider = get_ai_provider(mock_db)

        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "sk-test-key"

    def test_returns_anthropic_provider_when_configured(self):
        """Should return Anthropic provider when Anthropic is configured."""
        mock_db = MagicMock()
        config = AIConfigResponse(
            provider=AIProviderEnum.anthropic,
            api_key="sk-ant-test-key",
        )

        with patch(
            "app.services.ai.factory.SettingsService.get_ai_config",
            return_value=config,
        ):
            provider = get_ai_provider(mock_db)

        assert isinstance(provider, AnthropicProvider)
        assert provider.api_key == "sk-ant-test-key"

    def test_returns_gemini_provider_when_configured(self):
        """Should return Gemini provider when Gemini is configured."""
        mock_db = MagicMock()
        config = AIConfigResponse(
            provider=AIProviderEnum.gemini,
            api_key="AIza-test-key",
        )

        with patch(
            "app.services.ai.factory.SettingsService.get_ai_config",
            return_value=config,
        ):
            provider = get_ai_provider(mock_db)

        assert isinstance(provider, GeminiProvider)
        assert provider.api_key == "AIza-test-key"

    def test_raises_error_when_no_provider_configured(self):
        """Should raise AINotConfiguredError when no provider is set."""
        mock_db = MagicMock()

        with patch(
            "app.services.ai.factory.SettingsService.get_ai_config",
            return_value=None,
        ):
            with pytest.raises(AINotConfiguredError) as exc_info:
                get_ai_provider(mock_db)

        assert "No AI provider configured" in str(exc_info.value)

    def test_raises_error_when_api_key_not_set(self):
        """Should raise AINotConfiguredError when API key is missing."""
        mock_db = MagicMock()

        # get_ai_config returns None when provider is set but key is missing
        with patch(
            "app.services.ai.factory.SettingsService.get_ai_config",
            return_value=None,
        ):
            with pytest.raises(AINotConfiguredError) as exc_info:
                get_ai_provider(mock_db)

        assert "No AI provider configured" in str(exc_info.value)
