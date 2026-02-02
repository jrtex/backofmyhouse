import io
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.import_schemas import RecipeExtraction
from app.services.ai.base import AINotConfiguredError, AIExtractionError


def create_test_image(content: bytes = b"fake image content", filename: str = "test.jpg"):
    """Create a file-like object for testing uploads."""
    return {"file": (filename, io.BytesIO(content), "image/jpeg")}


def create_mock_extraction() -> RecipeExtraction:
    """Create a mock RecipeExtraction for testing."""
    return RecipeExtraction(
        title="Extracted Recipe",
        description="A delicious recipe",
        ingredients=[{"name": "Salt", "quantity": "1", "unit": "tsp"}],
        instructions=[{"step_number": 1, "text": "Mix well"}],
        prep_time_minutes=10,
        cook_time_minutes=20,
        servings=4,
        confidence=0.95,
        warnings=[],
    )


class TestImportImageEndpoint:
    """Tests for POST /api/import/image endpoint."""

    def test_import_image_requires_auth(self, client: TestClient):
        """Import image requires authentication."""
        files = create_test_image()
        response = client.post("/api/import/image", files=files)
        assert response.status_code == 401

    def test_import_image_invalid_file_type(
        self, client: TestClient, auth_headers: dict
    ):
        """Returns 400 for non-image file types."""
        files = {"file": ("test.txt", io.BytesIO(b"text content"), "text/plain")}
        response = client.post("/api/import/image", files=files, headers=auth_headers)
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_import_image_invalid_file_type_pdf(
        self, client: TestClient, auth_headers: dict
    ):
        """Returns 400 for PDF files."""
        files = {"file": ("test.pdf", io.BytesIO(b"pdf content"), "application/pdf")}
        response = client.post("/api/import/image", files=files, headers=auth_headers)
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_import_image_file_too_large(
        self, client: TestClient, auth_headers: dict
    ):
        """Returns 400 for files exceeding size limit."""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        files = {"file": ("large.jpg", io.BytesIO(large_content), "image/jpeg")}
        response = client.post("/api/import/image", files=files, headers=auth_headers)
        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    @patch("app.routers.import_router.get_ai_provider")
    def test_import_image_ai_not_configured(
        self, mock_get_provider, client: TestClient, auth_headers: dict
    ):
        """Returns 503 when AI provider is not configured."""
        mock_get_provider.side_effect = AINotConfiguredError(
            "No AI provider configured"
        )
        files = create_test_image()
        response = client.post("/api/import/image", files=files, headers=auth_headers)
        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()

    @patch("app.routers.import_router.get_ai_provider")
    def test_import_image_extraction_failure(
        self, mock_get_provider, client: TestClient, auth_headers: dict
    ):
        """Returns 422 when AI extraction fails."""
        mock_provider = Mock()
        mock_provider.extract_recipe_from_image = AsyncMock(
            side_effect=AIExtractionError("Could not extract recipe")
        )
        mock_get_provider.return_value = mock_provider

        files = create_test_image()
        response = client.post("/api/import/image", files=files, headers=auth_headers)
        assert response.status_code == 422
        assert "extract" in response.json()["detail"].lower()

    @patch("app.routers.import_router.get_ai_provider")
    def test_import_image_success(
        self, mock_get_provider, client: TestClient, auth_headers: dict
    ):
        """Successfully extracts recipe from image."""
        mock_extraction = create_mock_extraction()
        mock_provider = Mock()
        mock_provider.extract_recipe_from_image = AsyncMock(return_value=mock_extraction)
        mock_get_provider.return_value = mock_provider

        files = create_test_image()
        response = client.post("/api/import/image", files=files, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Extracted Recipe"
        assert data["confidence"] == 0.95
        assert len(data["ingredients"]) == 1
        assert len(data["instructions"]) == 1

    @patch("app.routers.import_router.get_ai_provider")
    def test_import_image_accepts_jpeg(
        self, mock_get_provider, client: TestClient, auth_headers: dict
    ):
        """Accepts JPEG images."""
        mock_extraction = create_mock_extraction()
        mock_provider = Mock()
        mock_provider.extract_recipe_from_image = AsyncMock(return_value=mock_extraction)
        mock_get_provider.return_value = mock_provider

        files = {"file": ("test.jpg", io.BytesIO(b"jpeg content"), "image/jpeg")}
        response = client.post("/api/import/image", files=files, headers=auth_headers)
        assert response.status_code == 200

    @patch("app.routers.import_router.get_ai_provider")
    def test_import_image_accepts_png(
        self, mock_get_provider, client: TestClient, auth_headers: dict
    ):
        """Accepts PNG images."""
        mock_extraction = create_mock_extraction()
        mock_provider = Mock()
        mock_provider.extract_recipe_from_image = AsyncMock(return_value=mock_extraction)
        mock_get_provider.return_value = mock_provider

        files = {"file": ("test.png", io.BytesIO(b"png content"), "image/png")}
        response = client.post("/api/import/image", files=files, headers=auth_headers)
        assert response.status_code == 200

    @patch("app.routers.import_router.get_ai_provider")
    def test_import_image_accepts_webp(
        self, mock_get_provider, client: TestClient, auth_headers: dict
    ):
        """Accepts WebP images."""
        mock_extraction = create_mock_extraction()
        mock_provider = Mock()
        mock_provider.extract_recipe_from_image = AsyncMock(return_value=mock_extraction)
        mock_get_provider.return_value = mock_provider

        files = {"file": ("test.webp", io.BytesIO(b"webp content"), "image/webp")}
        response = client.post("/api/import/image", files=files, headers=auth_headers)
        assert response.status_code == 200

    @patch("app.routers.import_router.get_ai_provider")
    def test_import_image_accepts_heic(
        self, mock_get_provider, client: TestClient, auth_headers: dict
    ):
        """Accepts HEIC images."""
        mock_extraction = create_mock_extraction()
        mock_provider = Mock()
        mock_provider.extract_recipe_from_image = AsyncMock(return_value=mock_extraction)
        mock_get_provider.return_value = mock_provider

        files = {"file": ("test.heic", io.BytesIO(b"heic content"), "image/heic")}
        response = client.post("/api/import/image", files=files, headers=auth_headers)
        assert response.status_code == 200

    @patch("app.routers.import_router.get_ai_provider")
    def test_import_image_passes_correct_mime_type(
        self, mock_get_provider, client: TestClient, auth_headers: dict
    ):
        """Passes correct MIME type to AI provider."""
        mock_extraction = create_mock_extraction()
        mock_provider = Mock()
        mock_provider.extract_recipe_from_image = AsyncMock(return_value=mock_extraction)
        mock_get_provider.return_value = mock_provider

        files = {"file": ("test.png", io.BytesIO(b"png content"), "image/png")}
        response = client.post("/api/import/image", files=files, headers=auth_headers)
        assert response.status_code == 200

        # Verify the provider was called with correct mime type
        mock_provider.extract_recipe_from_image.assert_called_once()
        call_args = mock_provider.extract_recipe_from_image.call_args
        assert call_args[1]["mime_type"] == "image/png"

    @patch("app.routers.import_router.get_ai_provider")
    def test_import_image_returns_warnings(
        self, mock_get_provider, client: TestClient, auth_headers: dict
    ):
        """Returns warnings from extraction."""
        mock_extraction = RecipeExtraction(
            title="Partial Recipe",
            ingredients=[],
            instructions=[],
            confidence=0.6,
            warnings=["Could not determine servings", "Instructions may be incomplete"],
        )
        mock_provider = Mock()
        mock_provider.extract_recipe_from_image = AsyncMock(return_value=mock_extraction)
        mock_get_provider.return_value = mock_provider

        files = create_test_image()
        response = client.post("/api/import/image", files=files, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["warnings"]) == 2
        assert data["confidence"] == 0.6


class TestImportUrlEndpoint:
    """Tests for POST /api/import/url endpoint."""

    def test_import_url_requires_auth(self, client: TestClient):
        """Import URL requires authentication."""
        response = client.post(
            "/api/import/url",
            json={"url": "https://example.com/recipe"},
        )
        assert response.status_code == 401

    def test_import_url_invalid_url_format(
        self, client: TestClient, auth_headers: dict
    ):
        """Returns 422 for invalid URL format."""
        response = client.post(
            "/api/import/url",
            json={"url": "not-a-valid-url"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_import_url_missing_url(
        self, client: TestClient, auth_headers: dict
    ):
        """Returns 422 when URL is missing."""
        response = client.post(
            "/api/import/url",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @patch("app.routers.import_router.UrlScraperService")
    def test_import_url_with_schema_org_success(
        self, mock_scraper_class, client: TestClient, auth_headers: dict
    ):
        """Successfully extracts recipe from URL with schema.org data."""
        from app.services.url_scraper import UrlContent

        mock_scraper = Mock()
        mock_scraper.fetch_url_content = AsyncMock(
            return_value=UrlContent(
                text="Recipe text content",
                schema_recipe={
                    "@type": "Recipe",
                    "name": "Schema.org Recipe",
                    "description": "A recipe with structured data",
                    "recipeIngredient": ["1 cup flour", "2 eggs"],
                    "recipeInstructions": [
                        {"@type": "HowToStep", "text": "Mix ingredients."},
                    ],
                    "prepTime": "PT15M",
                    "cookTime": "PT30M",
                    "recipeYield": "4 servings",
                },
                final_url="https://example.com/recipe",
            )
        )
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/import/url",
            json={"url": "https://example.com/recipe"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Schema.org Recipe"
        assert data["confidence"] == 0.9  # schema.org confidence
        assert len(data["ingredients"]) == 2
        assert len(data["instructions"]) == 1

    @patch("app.routers.import_router.get_ai_provider")
    @patch("app.routers.import_router.UrlScraperService")
    def test_import_url_falls_back_to_ai(
        self, mock_scraper_class, mock_get_provider, client: TestClient, auth_headers: dict
    ):
        """Falls back to AI extraction when no schema.org data."""
        from app.services.url_scraper import UrlContent

        mock_scraper = Mock()
        mock_scraper.fetch_url_content = AsyncMock(
            return_value=UrlContent(
                text="Grandma's Apple Pie\n\nIngredients:\n- 6 apples\n- 1 cup sugar",
                schema_recipe=None,  # No schema.org data
                final_url="https://example.com/recipe",
            )
        )
        mock_scraper_class.return_value = mock_scraper

        mock_extraction = create_mock_extraction()
        mock_extraction.title = "AI Extracted Recipe"
        mock_provider = Mock()
        mock_provider.extract_recipe_from_text = AsyncMock(return_value=mock_extraction)
        mock_get_provider.return_value = mock_provider

        response = client.post(
            "/api/import/url",
            json={"url": "https://example.com/recipe"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "AI Extracted Recipe"
        # Verify AI provider was called with the text
        mock_provider.extract_recipe_from_text.assert_called_once()

    @patch("app.routers.import_router.get_ai_provider")
    @patch("app.routers.import_router.UrlScraperService")
    def test_import_url_ai_not_configured_on_fallback(
        self, mock_scraper_class, mock_get_provider, client: TestClient, auth_headers: dict
    ):
        """Returns 503 when AI fallback needed but not configured."""
        from app.services.url_scraper import UrlContent

        mock_scraper = Mock()
        mock_scraper.fetch_url_content = AsyncMock(
            return_value=UrlContent(
                text="Recipe text",
                schema_recipe=None,  # No schema.org data, needs AI
                final_url="https://example.com/recipe",
            )
        )
        mock_scraper_class.return_value = mock_scraper

        mock_get_provider.side_effect = AINotConfiguredError("No AI configured")

        response = client.post(
            "/api/import/url",
            json={"url": "https://example.com/recipe"},
            headers=auth_headers,
        )
        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()

    @patch("app.routers.import_router.UrlScraperService")
    def test_import_url_fetch_error(
        self, mock_scraper_class, client: TestClient, auth_headers: dict
    ):
        """Returns 422 when URL fetch fails."""
        from app.services.url_scraper import UrlFetchError

        mock_scraper = Mock()
        mock_scraper.fetch_url_content = AsyncMock(
            side_effect=UrlFetchError("Page not found (404)")
        )
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/import/url",
            json={"url": "https://example.com/missing"},
            headers=auth_headers,
        )
        assert response.status_code == 422
        assert "404" in response.json()["detail"] or "fetch" in response.json()["detail"].lower()

    @patch("app.routers.import_router.UrlScraperService")
    def test_import_url_blocked_error(
        self, mock_scraper_class, client: TestClient, auth_headers: dict
    ):
        """Returns 422 when URL access is blocked."""
        from app.services.url_scraper import UrlBlockedError

        mock_scraper = Mock()
        mock_scraper.fetch_url_content = AsyncMock(
            side_effect=UrlBlockedError("Access blocked (403 Forbidden)")
        )
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/import/url",
            json={"url": "https://blocked-site.com/recipe"},
            headers=auth_headers,
        )
        assert response.status_code == 422
        assert "blocked" in response.json()["detail"].lower() or "403" in response.json()["detail"]

    @patch("app.routers.import_router.get_ai_provider")
    @patch("app.routers.import_router.UrlScraperService")
    def test_import_url_ai_extraction_failure(
        self, mock_scraper_class, mock_get_provider, client: TestClient, auth_headers: dict
    ):
        """Returns 422 when AI extraction fails."""
        from app.services.url_scraper import UrlContent

        mock_scraper = Mock()
        mock_scraper.fetch_url_content = AsyncMock(
            return_value=UrlContent(
                text="Some text",
                schema_recipe=None,
                final_url="https://example.com/recipe",
            )
        )
        mock_scraper_class.return_value = mock_scraper

        mock_provider = Mock()
        mock_provider.extract_recipe_from_text = AsyncMock(
            side_effect=AIExtractionError("Could not extract recipe")
        )
        mock_get_provider.return_value = mock_provider

        response = client.post(
            "/api/import/url",
            json={"url": "https://example.com/recipe"},
            headers=auth_headers,
        )
        assert response.status_code == 422
        assert "extract" in response.json()["detail"].lower()

    @patch("app.routers.import_router.UrlScraperService")
    def test_import_url_schema_org_no_ai_needed(
        self, mock_scraper_class, client: TestClient, auth_headers: dict
    ):
        """Does not call AI provider when schema.org data is found."""
        from app.services.url_scraper import UrlContent

        mock_scraper = Mock()
        mock_scraper.fetch_url_content = AsyncMock(
            return_value=UrlContent(
                text="Recipe text",
                schema_recipe={
                    "@type": "Recipe",
                    "name": "Simple Recipe",
                },
                final_url="https://example.com/recipe",
            )
        )
        mock_scraper_class.return_value = mock_scraper

        # Note: not patching get_ai_provider - if it's called, test will fail
        response = client.post(
            "/api/import/url",
            json={"url": "https://example.com/recipe"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Simple Recipe"
