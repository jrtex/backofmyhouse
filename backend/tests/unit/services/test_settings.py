import pytest
from unittest.mock import patch, AsyncMock

from app.services.settings import SettingsService
from app.schemas.settings import (
    AIProvider,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_GEMINI_MODEL,
)


class TestGetSetting:
    def test_get_setting_nonexistent(self, db):
        """Getting a nonexistent setting returns None."""
        result = SettingsService.get_setting(db, "nonexistent_key")
        assert result is None

    def test_get_setting_unencrypted(self, db):
        """Getting an unencrypted setting returns the value."""
        SettingsService.set_setting(db, "test_key", "test_value", encrypt=False)
        result = SettingsService.get_setting(db, "test_key")
        assert result == "test_value"

    def test_get_setting_encrypted(self, db):
        """Getting an encrypted setting returns decrypted value."""
        SettingsService.set_setting(db, "api_key", "secret-key-123", encrypt=True)
        result = SettingsService.get_setting(db, "api_key")
        assert result == "secret-key-123"


class TestSetSetting:
    def test_set_setting_creates_new(self, db):
        """Setting a new key creates a new record."""
        SettingsService.set_setting(db, "new_key", "new_value")
        result = SettingsService.get_setting(db, "new_key")
        assert result == "new_value"

    def test_set_setting_updates_existing(self, db):
        """Setting an existing key updates the value."""
        SettingsService.set_setting(db, "my_key", "original")
        SettingsService.set_setting(db, "my_key", "updated")
        result = SettingsService.get_setting(db, "my_key")
        assert result == "updated"

    def test_set_setting_encrypted(self, db):
        """Setting an encrypted value stores it encrypted."""
        from app.models.app_setting import AppSetting

        SettingsService.set_setting(db, "secret", "my-secret", encrypt=True)

        # Check the raw database value is not the plaintext
        setting = db.query(AppSetting).filter(AppSetting.key == "secret").first()
        assert setting.value != "my-secret"
        assert setting.is_encrypted is True

        # But getting it decrypts it
        result = SettingsService.get_setting(db, "secret")
        assert result == "my-secret"

    def test_set_setting_none_deletes(self, db):
        """Setting a value to None deletes the setting."""
        SettingsService.set_setting(db, "to_delete", "value")
        assert SettingsService.get_setting(db, "to_delete") == "value"

        SettingsService.set_setting(db, "to_delete", None)
        assert SettingsService.get_setting(db, "to_delete") is None


class TestGetAllSettings:
    def test_get_all_settings_empty(self, db):
        """With no settings, returns defaults."""
        result = SettingsService.get_all_settings(db)
        assert result.ai_provider is None
        assert result.openai_api_key_configured is False
        assert result.anthropic_api_key_configured is False
        assert result.gemini_api_key_configured is False
        assert result.openai_model == DEFAULT_OPENAI_MODEL
        assert result.anthropic_model == DEFAULT_ANTHROPIC_MODEL
        assert result.gemini_model == DEFAULT_GEMINI_MODEL

    def test_get_all_settings_with_provider(self, db):
        """Returns configured AI provider."""
        SettingsService.set_setting(db, SettingsService.AI_PROVIDER_KEY, "openai")
        result = SettingsService.get_all_settings(db)
        assert result.ai_provider == AIProvider.openai

    def test_get_all_settings_with_api_keys(self, db):
        """Shows which API keys are configured."""
        SettingsService.set_setting(
            db, SettingsService.OPENAI_API_KEY, "sk-test", encrypt=True
        )
        SettingsService.set_setting(
            db, SettingsService.GEMINI_API_KEY, "AIza-test", encrypt=True
        )

        result = SettingsService.get_all_settings(db)
        assert result.openai_api_key_configured is True
        assert result.anthropic_api_key_configured is False
        assert result.gemini_api_key_configured is True


class TestGetAIConfig:
    def test_get_ai_config_not_configured(self, db):
        """Returns None when no provider is configured."""
        result = SettingsService.get_ai_config(db)
        assert result is None

    def test_get_ai_config_provider_no_key(self, db):
        """Returns None when provider is set but key is missing."""
        SettingsService.set_setting(db, SettingsService.AI_PROVIDER_KEY, "openai")
        result = SettingsService.get_ai_config(db)
        assert result is None

    def test_get_ai_config_complete(self, db):
        """Returns provider, decrypted key, and model when configured."""
        SettingsService.set_setting(db, SettingsService.AI_PROVIDER_KEY, "anthropic")
        SettingsService.set_setting(
            db, SettingsService.ANTHROPIC_API_KEY, "sk-ant-secret", encrypt=True
        )

        result = SettingsService.get_ai_config(db)
        assert result is not None
        assert result.provider == AIProvider.anthropic
        assert result.api_key == "sk-ant-secret"
        assert result.model == DEFAULT_ANTHROPIC_MODEL

    def test_get_ai_config_with_custom_model(self, db):
        """Returns custom model when configured."""
        SettingsService.set_setting(db, SettingsService.AI_PROVIDER_KEY, "gemini")
        SettingsService.set_setting(
            db, SettingsService.GEMINI_API_KEY, "AIza-secret", encrypt=True
        )
        SettingsService.set_setting(db, SettingsService.GEMINI_MODEL_KEY, "gemini-1.5-pro")

        result = SettingsService.get_ai_config(db)
        assert result is not None
        assert result.provider == AIProvider.gemini
        assert result.model == "gemini-1.5-pro"


class TestValidateAPIKey:
    @pytest.mark.asyncio
    @patch("app.services.settings.httpx.AsyncClient")
    async def test_validate_openai_key_valid(self, mock_client_class):
        """Valid OpenAI key returns True."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value.status_code = 200
        mock_client_class.return_value = mock_client

        result = await SettingsService.validate_api_key("openai", "sk-valid-key")
        assert result is True

    @pytest.mark.asyncio
    @patch("app.services.settings.httpx.AsyncClient")
    async def test_validate_openai_key_invalid(self, mock_client_class):
        """Invalid OpenAI key returns False."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value.status_code = 401
        mock_client_class.return_value = mock_client

        result = await SettingsService.validate_api_key("openai", "invalid-key")
        assert result is False

    @pytest.mark.asyncio
    @patch("app.services.settings.httpx.AsyncClient")
    async def test_validate_anthropic_key_valid(self, mock_client_class):
        """Valid Anthropic key returns True."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value.status_code = 200
        mock_client_class.return_value = mock_client

        result = await SettingsService.validate_api_key("anthropic", "sk-ant-valid")
        assert result is True

    @pytest.mark.asyncio
    @patch("app.services.settings.httpx.AsyncClient")
    async def test_validate_gemini_key_valid(self, mock_client_class):
        """Valid Gemini key returns True."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value.status_code = 200
        mock_client_class.return_value = mock_client

        result = await SettingsService.validate_api_key("gemini", "AIza-valid")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_unknown_provider(self):
        """Unknown provider returns False."""
        result = await SettingsService.validate_api_key("unknown", "any-key")
        assert result is False

    @pytest.mark.asyncio
    @patch("app.services.settings.httpx.AsyncClient")
    async def test_validate_key_network_error(self, mock_client_class):
        """Network error returns False."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client

        result = await SettingsService.validate_api_key("openai", "sk-key")
        assert result is False
