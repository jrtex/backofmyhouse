"""URL scraper service for fetching and parsing recipe web pages."""

import json
from dataclasses import dataclass
from typing import Optional

import httpx
from bs4 import BeautifulSoup


class UrlFetchError(Exception):
    """Raised when URL fetching fails."""

    pass


class UrlBlockedError(Exception):
    """Raised when access to URL is blocked (403/429)."""

    pass


@dataclass
class UrlContent:
    """Result of fetching and parsing a URL."""

    text: str  # Visible text extracted from HTML
    schema_recipe: Optional[dict]  # schema.org Recipe if found
    final_url: str  # URL after any redirects


# Maximum text length to return (for AI context window)
MAX_TEXT_LENGTH = 15000

# Request timeout in seconds
REQUEST_TIMEOUT = 30.0

# User agent to identify as a recipe import tool
USER_AGENT = "RecipeImporter/1.0 (Recipe Management App; +https://github.com/jrtex/backofmyhouse)"

# Tags to remove from HTML before text extraction
TAGS_TO_REMOVE = ["script", "style", "nav", "header", "footer", "aside", "noscript"]


class UrlScraperService:
    """Service for fetching and parsing recipe URLs."""

    async def fetch_url_content(self, url: str) -> UrlContent:
        """Fetch URL content and extract recipe data.

        Args:
            url: The URL to fetch.

        Returns:
            UrlContent with extracted text and optional schema.org data.

        Raises:
            UrlFetchError: If the URL cannot be fetched.
            UrlBlockedError: If access is blocked (403/429).
        """
        headers = {"User-Agent": USER_AGENT}

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                max_redirects=5,
                timeout=REQUEST_TIMEOUT,
            ) as client:
                response = await client.get(url, headers=headers)
        except httpx.TimeoutException:
            raise UrlFetchError(f"Request timeout after {REQUEST_TIMEOUT} seconds")
        except httpx.ConnectError as e:
            raise UrlFetchError(f"Failed to connect to URL: {e}")
        except httpx.RequestError as e:
            raise UrlFetchError(f"Failed to fetch URL: {e}")

        # Handle error status codes
        if response.status_code == 403:
            raise UrlBlockedError("Access blocked (403 Forbidden)")
        if response.status_code == 429:
            raise UrlBlockedError("Rate limited (429 Too Many Requests)")
        if response.status_code == 404:
            raise UrlFetchError("Page not found (404)")
        if response.status_code >= 500:
            raise UrlFetchError(f"Server error ({response.status_code})")
        if response.status_code >= 400:
            raise UrlFetchError(f"HTTP error ({response.status_code})")

        html = response.text
        final_url = str(response.url)

        # Extract schema.org recipe data if present
        schema_recipe = self.extract_schema_org_recipe(html)

        # Extract visible text from HTML
        text = self._extract_visible_text(html)

        return UrlContent(
            text=text,
            schema_recipe=schema_recipe,
            final_url=final_url,
        )

    def extract_schema_org_recipe(self, html: str) -> Optional[dict]:
        """Extract schema.org Recipe data from HTML.

        Looks for JSON-LD script tags containing Recipe schema.

        Args:
            html: The HTML content to parse.

        Returns:
            Recipe dict if found, None otherwise.
        """
        soup = BeautifulSoup(html, "lxml")

        # Find all JSON-LD script tags
        json_ld_scripts = soup.find_all("script", type="application/ld+json")

        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
            except (json.JSONDecodeError, TypeError):
                continue

            # Check for direct Recipe type
            if isinstance(data, dict):
                recipe = self._find_recipe_in_data(data)
                if recipe:
                    return recipe

            # Check for array of items
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        recipe = self._find_recipe_in_data(item)
                        if recipe:
                            return recipe

        return None

    def _find_recipe_in_data(self, data: dict) -> Optional[dict]:
        """Find Recipe object in schema.org data structure.

        Args:
            data: JSON-LD data dict to search.

        Returns:
            Recipe dict if found, None otherwise.
        """
        # Direct Recipe type
        if data.get("@type") == "Recipe":
            return data

        # Recipe in @graph array
        if "@graph" in data and isinstance(data["@graph"], list):
            for item in data["@graph"]:
                if isinstance(item, dict) and item.get("@type") == "Recipe":
                    return item

        return None

    def _extract_visible_text(self, html: str) -> str:
        """Extract visible text from HTML, removing unwanted elements.

        Args:
            html: The HTML content to parse.

        Returns:
            Cleaned visible text, truncated to MAX_TEXT_LENGTH.
        """
        soup = BeautifulSoup(html, "lxml")

        # Remove unwanted tags
        for tag in TAGS_TO_REMOVE:
            for element in soup.find_all(tag):
                element.decompose()

        # Extract text with newline separators
        text = soup.get_text(separator="\n", strip=True)

        # Clean up multiple newlines
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)

        # Truncate if too long
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]

        return text
