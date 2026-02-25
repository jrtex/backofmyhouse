import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.settings import SettingsService


class TestGetSettings:
    def test_get_settings_as_admin(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Admin can get settings."""
        response = client.get("/api/settings", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "ai_provider" in data
        assert "openai_api_key_configured" in data
        assert "anthropic_api_key_configured" in data
        assert "gemini_api_key_configured" in data
        assert "openai_model" in data
        assert "anthropic_model" in data
        assert "gemini_model" in data

    def test_get_settings_as_standard_user(
        self, client: TestClient, auth_headers: dict
    ):
        """Standard user cannot get settings."""
        response = client.get("/api/settings", headers=auth_headers)
        assert response.status_code == 403

    def test_get_settings_requires_auth(self, client: TestClient):
        """Get settings requires authentication."""
        response = client.get("/api/settings")
        assert response.status_code == 401

    def test_get_settings_shows_configured_keys(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Settings response shows which API keys are configured."""
        # Configure an API key
        SettingsService.set_setting(
            db, SettingsService.OPENAI_API_KEY, "sk-test-key", encrypt=True
        )

        response = client.get("/api/settings", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["openai_api_key_configured"] is True
        assert data["anthropic_api_key_configured"] is False


class TestTestConnection:
    @patch("app.services.settings.SettingsService.validate_api_key")
    def test_test_connection_with_provided_key(
        self, mock_validate, client: TestClient, admin_auth_headers: dict
    ):
        """Test connection with a provided API key."""
        mock_validate.return_value = True

        response = client.post(
            "/api/settings/test-connection",
            json={"provider": "openai", "api_key": "sk-test-key"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Connection successful"

    @patch("app.services.settings.SettingsService.validate_api_key")
    def test_test_connection_with_stored_key(
        self, mock_validate, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Test connection using stored API key."""
        mock_validate.return_value = True
        SettingsService.set_setting(
            db, SettingsService.OPENAI_API_KEY, "sk-stored", encrypt=True
        )

        response = client.post(
            "/api/settings/test-connection",
            json={"provider": "openai"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_test_connection_no_key_configured(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Test connection fails when no key is stored and none provided."""
        response = client.post(
            "/api/settings/test-connection",
            json={"provider": "openai"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No API key configured" in data["message"]

    @patch("app.services.settings.SettingsService.validate_api_key")
    def test_test_connection_invalid_key(
        self, mock_validate, client: TestClient, admin_auth_headers: dict
    ):
        """Test connection with an invalid API key."""
        mock_validate.return_value = False

        response = client.post(
            "/api/settings/test-connection",
            json={"provider": "openai", "api_key": "invalid"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Connection failed" in data["message"]

    def test_test_connection_requires_admin(
        self, client: TestClient, auth_headers: dict
    ):
        """Standard user cannot test connection."""
        response = client.post(
            "/api/settings/test-connection",
            json={"provider": "openai", "api_key": "sk-test"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_test_connection_requires_auth(self, client: TestClient):
        """Test connection requires authentication."""
        response = client.post(
            "/api/settings/test-connection",
            json={"provider": "openai", "api_key": "sk-test"},
        )
        assert response.status_code == 401


class TestUpdateSettings:
    def test_update_ai_provider(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Admin can update AI provider."""
        response = client.put(
            "/api/settings",
            json={"ai_provider": "openai"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["ai_provider"] == "openai"

        # Verify persisted
        response = client.get("/api/settings", headers=admin_auth_headers)
        assert response.json()["ai_provider"] == "openai"

    def test_update_ai_provider_invalid(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Invalid AI provider returns 422."""
        response = client.put(
            "/api/settings",
            json={"ai_provider": "invalid_provider"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    @patch("app.services.settings.SettingsService.validate_api_key")
    def test_update_api_key_valid(
        self, mock_validate, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Admin can update API key when valid."""
        mock_validate.return_value = True

        response = client.put(
            "/api/settings",
            json={"openai_api_key": "sk-test123"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["openai_api_key_configured"] is True

        # Verify the key was actually stored (encrypted)
        stored_key = SettingsService.get_setting(db, SettingsService.OPENAI_API_KEY)
        assert stored_key == "sk-test123"

    @patch("app.services.settings.SettingsService.validate_api_key")
    def test_update_api_key_invalid(
        self, mock_validate, client: TestClient, admin_auth_headers: dict
    ):
        """Invalid API key returns 400."""
        mock_validate.return_value = False

        response = client.put(
            "/api/settings",
            json={"openai_api_key": "invalid-key"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
        assert "Invalid OPENAI API key" in response.json()["detail"]

    @patch("app.services.settings.SettingsService.validate_api_key")
    def test_update_multiple_settings(
        self, mock_validate, client: TestClient, admin_auth_headers: dict
    ):
        """Can update provider and API key together."""
        mock_validate.return_value = True

        response = client.put(
            "/api/settings",
            json={
                "ai_provider": "anthropic",
                "anthropic_api_key": "sk-ant-test",
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ai_provider"] == "anthropic"
        assert data["anthropic_api_key_configured"] is True

    def test_update_settings_as_standard_user(
        self, client: TestClient, auth_headers: dict
    ):
        """Standard user cannot update settings."""
        response = client.put(
            "/api/settings",
            json={"ai_provider": "openai"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_update_settings_requires_auth(self, client: TestClient):
        """Update settings requires authentication."""
        response = client.put(
            "/api/settings",
            json={"ai_provider": "openai"},
        )
        assert response.status_code == 401

    @patch("app.services.settings.SettingsService.validate_api_key")
    def test_update_preserves_existing_keys(
        self, mock_validate, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Updating one setting doesn't affect others."""
        mock_validate.return_value = True

        # Set initial API key
        client.put(
            "/api/settings",
            json={"openai_api_key": "sk-original"},
            headers=admin_auth_headers,
        )

        # Update only the provider
        response = client.put(
            "/api/settings",
            json={"ai_provider": "openai"},
            headers=admin_auth_headers,
        )

        # Original key should still be configured
        assert response.status_code == 200
        data = response.json()
        assert data["openai_api_key_configured"] is True

    @patch("app.services.settings.SettingsService.validate_api_key")
    def test_api_keys_not_returned_in_response(
        self, mock_validate, client: TestClient, admin_auth_headers: dict
    ):
        """API key values are never returned, only configured status."""
        mock_validate.return_value = True

        response = client.put(
            "/api/settings",
            json={"openai_api_key": "sk-secret-key"},
            headers=admin_auth_headers,
        )

        data = response.json()
        # Should not contain the actual key
        assert "sk-secret-key" not in str(data)
        # Should only show configured status
        assert "openai_api_key_configured" in data
        assert "openai_api_key" not in data

    def test_update_model_names(
        self, client: TestClient, admin_auth_headers: dict, db: Session
    ):
        """Admin can update model names."""
        response = client.put(
            "/api/settings",
            json={
                "openai_model": "gpt-4o",
                "gemini_model": "gemini-2.5-pro",
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["openai_model"] == "gpt-4o"
        assert data["gemini_model"] == "gemini-2.5-pro"

        # Verify persisted
        response = client.get("/api/settings", headers=admin_auth_headers)
        data = response.json()
        assert data["openai_model"] == "gpt-4o"
        assert data["gemini_model"] == "gemini-2.5-pro"
