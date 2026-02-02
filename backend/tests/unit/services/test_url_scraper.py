"""Unit tests for URL scraper service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.url_scraper import (
    UrlScraperService,
    UrlContent,
    UrlFetchError,
    UrlBlockedError,
)


# Sample HTML with schema.org JSON-LD recipe
HTML_WITH_SCHEMA_ORG = """
<!DOCTYPE html>
<html>
<head>
    <title>Chocolate Chip Cookies</title>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org/",
        "@type": "Recipe",
        "name": "Chocolate Chip Cookies",
        "description": "Classic homemade cookies",
        "recipeIngredient": [
            "2 1/4 cups all-purpose flour",
            "1 cup butter, softened",
            "2 cups chocolate chips"
        ],
        "recipeInstructions": [
            {"@type": "HowToStep", "text": "Preheat oven to 375F."},
            {"@type": "HowToStep", "text": "Mix ingredients."},
            {"@type": "HowToStep", "text": "Bake for 10 minutes."}
        ],
        "prepTime": "PT15M",
        "cookTime": "PT10M",
        "recipeYield": "24 cookies"
    }
    </script>
</head>
<body>
    <nav>Navigation</nav>
    <header>Header</header>
    <main>
        <h1>Chocolate Chip Cookies</h1>
        <p>Classic homemade cookies recipe.</p>
    </main>
    <footer>Footer</footer>
</body>
</html>
"""

# Sample HTML without schema.org
HTML_WITHOUT_SCHEMA_ORG = """
<!DOCTYPE html>
<html>
<head><title>Simple Recipe Page</title></head>
<body>
    <script>console.log('test');</script>
    <style>.hidden { display: none; }</style>
    <nav>Navigation links</nav>
    <main>
        <h1>Grandma's Apple Pie</h1>
        <p>A delicious apple pie recipe.</p>
        <h2>Ingredients</h2>
        <ul>
            <li>6 apples</li>
            <li>1 cup sugar</li>
        </ul>
        <h2>Instructions</h2>
        <ol>
            <li>Peel and slice apples.</li>
            <li>Mix with sugar.</li>
        </ol>
    </main>
    <footer>Copyright 2024</footer>
</body>
</html>
"""


class TestUrlScraperService:
    """Tests for the URL scraper service."""

    @pytest.mark.asyncio
    async def test_fetch_url_with_schema_org_data(self):
        """Should extract schema.org recipe data when present."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = HTML_WITH_SCHEMA_ORG
        mock_response.url = httpx.URL("https://example.com/recipe")

        with patch("app.services.url_scraper.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            service = UrlScraperService()
            result = await service.fetch_url_content("https://example.com/recipe")

        assert isinstance(result, UrlContent)
        assert result.schema_recipe is not None
        assert result.schema_recipe["name"] == "Chocolate Chip Cookies"
        assert result.schema_recipe["@type"] == "Recipe"
        assert len(result.schema_recipe["recipeIngredient"]) == 3
        assert result.final_url == "https://example.com/recipe"

    @pytest.mark.asyncio
    async def test_fetch_url_without_schema_org_data(self):
        """Should return None for schema_recipe when no schema.org data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = HTML_WITHOUT_SCHEMA_ORG
        mock_response.url = httpx.URL("https://example.com/simple")

        with patch("app.services.url_scraper.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            service = UrlScraperService()
            result = await service.fetch_url_content("https://example.com/simple")

        assert isinstance(result, UrlContent)
        assert result.schema_recipe is None
        assert result.text is not None
        assert "Grandma's Apple Pie" in result.text

    @pytest.mark.asyncio
    async def test_extracts_visible_text_only(self):
        """Should extract visible text and exclude scripts, styles, nav, etc."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = HTML_WITHOUT_SCHEMA_ORG
        mock_response.url = httpx.URL("https://example.com/recipe")

        with patch("app.services.url_scraper.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            service = UrlScraperService()
            result = await service.fetch_url_content("https://example.com/recipe")

        # Should not contain script/style content
        assert "console.log" not in result.text
        assert ".hidden" not in result.text
        # Should not contain nav/footer content (or minimal)
        assert "Navigation links" not in result.text
        assert "Copyright 2024" not in result.text
        # Should contain main content
        assert "Grandma's Apple Pie" in result.text
        assert "6 apples" in result.text

    @pytest.mark.asyncio
    async def test_handles_redirects(self):
        """Should follow redirects and return final URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = HTML_WITHOUT_SCHEMA_ORG
        # Final URL after redirect
        mock_response.url = httpx.URL("https://www.example.com/recipe/123")

        with patch("app.services.url_scraper.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            service = UrlScraperService()
            result = await service.fetch_url_content("https://example.com/recipe")

        assert result.final_url == "https://www.example.com/recipe/123"

    @pytest.mark.asyncio
    async def test_raises_on_timeout(self):
        """Should raise UrlFetchError on request timeout."""
        with patch("app.services.url_scraper.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            service = UrlScraperService()
            with pytest.raises(UrlFetchError) as exc_info:
                await service.fetch_url_content("https://slow-site.com/recipe")

        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_raises_on_connection_error(self):
        """Should raise UrlFetchError on connection failure."""
        with patch("app.services.url_scraper.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            service = UrlScraperService()
            with pytest.raises(UrlFetchError) as exc_info:
                await service.fetch_url_content("https://invalid-site.com/recipe")

        assert "connect" in str(exc_info.value).lower() or "fetch" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_raises_on_403_forbidden(self):
        """Should raise UrlBlockedError on 403 status."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        with patch("app.services.url_scraper.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            service = UrlScraperService()
            with pytest.raises(UrlBlockedError) as exc_info:
                await service.fetch_url_content("https://blocked-site.com/recipe")

        assert "403" in str(exc_info.value) or "blocked" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_raises_on_429_rate_limited(self):
        """Should raise UrlBlockedError on 429 status."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"

        with patch("app.services.url_scraper.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            service = UrlScraperService()
            with pytest.raises(UrlBlockedError) as exc_info:
                await service.fetch_url_content("https://rate-limited.com/recipe")

        assert "429" in str(exc_info.value) or "rate" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_raises_on_404_not_found(self):
        """Should raise UrlFetchError on 404 status."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        with patch("app.services.url_scraper.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            service = UrlScraperService()
            with pytest.raises(UrlFetchError) as exc_info:
                await service.fetch_url_content("https://example.com/missing")

        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_raises_on_500_server_error(self):
        """Should raise UrlFetchError on 500 status."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("app.services.url_scraper.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            service = UrlScraperService()
            with pytest.raises(UrlFetchError) as exc_info:
                await service.fetch_url_content("https://broken-site.com/recipe")

        assert "500" in str(exc_info.value) or "server error" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_truncates_long_text(self):
        """Should truncate text to maximum length."""
        # Create HTML with very long content
        long_content = "Recipe content. " * 5000  # ~80,000 chars
        html = f"<html><body><main>{long_content}</main></body></html>"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html
        mock_response.url = httpx.URL("https://example.com/recipe")

        with patch("app.services.url_scraper.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            service = UrlScraperService()
            result = await service.fetch_url_content("https://example.com/recipe")

        # Should be truncated to max length (15000 chars)
        assert len(result.text) <= 15000

    @pytest.mark.asyncio
    async def test_uses_proper_user_agent(self):
        """Should set a proper User-Agent header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = HTML_WITHOUT_SCHEMA_ORG
        mock_response.url = httpx.URL("https://example.com/recipe")

        with patch("app.services.url_scraper.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            service = UrlScraperService()
            await service.fetch_url_content("https://example.com/recipe")

            # Check that headers were passed with User-Agent
            call_kwargs = mock_client.get.call_args
            headers = call_kwargs.kwargs.get("headers", {})
            assert "User-Agent" in headers or any(
                "user-agent" in str(k).lower() for k in headers.keys()
            )


class TestExtractSchemaOrgRecipe:
    """Tests for schema.org extraction helper."""

    def test_extracts_json_ld_recipe(self):
        """Should extract Recipe from JSON-LD script tag."""
        service = UrlScraperService()
        result = service.extract_schema_org_recipe(HTML_WITH_SCHEMA_ORG)

        assert result is not None
        assert result["@type"] == "Recipe"
        assert result["name"] == "Chocolate Chip Cookies"

    def test_returns_none_when_no_recipe(self):
        """Should return None when no schema.org Recipe found."""
        service = UrlScraperService()
        result = service.extract_schema_org_recipe(HTML_WITHOUT_SCHEMA_ORG)

        assert result is None

    def test_handles_recipe_in_graph(self):
        """Should find Recipe within @graph array."""
        html_with_graph = """
        <html>
        <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "WebPage", "name": "Recipe Page"},
                {"@type": "Recipe", "name": "Pasta Carbonara", "recipeIngredient": ["pasta", "eggs"]}
            ]
        }
        </script>
        </head>
        </html>
        """
        service = UrlScraperService()
        result = service.extract_schema_org_recipe(html_with_graph)

        assert result is not None
        assert result["@type"] == "Recipe"
        assert result["name"] == "Pasta Carbonara"

    def test_handles_multiple_json_ld_scripts(self):
        """Should find Recipe even if multiple JSON-LD scripts exist."""
        html_multiple = """
        <html>
        <head>
        <script type="application/ld+json">{"@type": "Organization", "name": "Test"}</script>
        <script type="application/ld+json">{"@type": "Recipe", "name": "Found Recipe"}</script>
        </head>
        </html>
        """
        service = UrlScraperService()
        result = service.extract_schema_org_recipe(html_multiple)

        assert result is not None
        assert result["name"] == "Found Recipe"

    def test_handles_malformed_json_ld(self):
        """Should return None for malformed JSON-LD."""
        html_bad_json = """
        <html>
        <head>
        <script type="application/ld+json">not valid json{</script>
        </head>
        </html>
        """
        service = UrlScraperService()
        result = service.extract_schema_org_recipe(html_bad_json)

        assert result is None
