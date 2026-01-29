import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.import_schemas import RecipeExtraction
from app.services.ai import (
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    AIExtractionError,
)


# Sample valid extraction response data
SAMPLE_EXTRACTION_DATA = {
    "title": "Chocolate Chip Cookies",
    "description": "Classic homemade chocolate chip cookies",
    "ingredients": [
        {"name": "all-purpose flour", "quantity": "2 1/4", "unit": "cups", "notes": None},
        {"name": "butter", "quantity": "1", "unit": "cup", "notes": "softened"},
        {"name": "chocolate chips", "quantity": "2", "unit": "cups", "notes": None},
    ],
    "instructions": [
        {"step_number": 1, "text": "Preheat oven to 375°F."},
        {"step_number": 2, "text": "Mix flour, butter, and sugar."},
        {"step_number": 3, "text": "Fold in chocolate chips."},
    ],
    "prep_time_minutes": 15,
    "cook_time_minutes": 10,
    "servings": 24,
    "notes": "Store in airtight container",
    "special_equipment": ["stand mixer"],
    "confidence": 0.95,
    "warnings": [],
}

SAMPLE_IMAGE_DATA = b"fake image data"
SAMPLE_MIME_TYPE = "image/jpeg"
SAMPLE_TEXT = "Recipe: Chocolate Chip Cookies..."


class TestOpenAIProvider:
    """Tests for the OpenAI provider implementation."""

    @pytest.mark.asyncio
    async def test_extract_recipe_from_image_success(self):
        """Should successfully extract recipe from image."""
        provider = OpenAIProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(SAMPLE_EXTRACTION_DATA)))
        ]

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.extract_recipe_from_image(
                SAMPLE_IMAGE_DATA, SAMPLE_MIME_TYPE
            )

        assert isinstance(result, RecipeExtraction)
        assert result.title == "Chocolate Chip Cookies"
        assert len(result.ingredients) == 3
        assert len(result.instructions) == 3
        assert result.confidence == 0.95

    @pytest.mark.asyncio
    async def test_extract_recipe_from_text_success(self):
        """Should successfully extract recipe from text."""
        provider = OpenAIProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(SAMPLE_EXTRACTION_DATA)))
        ]

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.extract_recipe_from_text(SAMPLE_TEXT)

        assert isinstance(result, RecipeExtraction)
        assert result.title == "Chocolate Chip Cookies"

    @pytest.mark.asyncio
    async def test_extract_recipe_raises_on_empty_response(self):
        """Should raise AIExtractionError on empty response."""
        provider = OpenAIProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(AIExtractionError) as exc_info:
                await provider.extract_recipe_from_image(
                    SAMPLE_IMAGE_DATA, SAMPLE_MIME_TYPE
                )

        assert "Empty response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_recipe_raises_on_invalid_json(self):
        """Should raise AIExtractionError on invalid JSON response."""
        provider = OpenAIProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="not valid json"))
        ]

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(AIExtractionError) as exc_info:
                await provider.extract_recipe_from_text(SAMPLE_TEXT)

        assert "Failed to parse JSON" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_recipe_raises_on_api_error(self):
        """Should raise AIExtractionError on API error."""
        provider = OpenAIProvider(api_key="sk-test")

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=Exception("API rate limit exceeded"),
        ):
            with pytest.raises(AIExtractionError) as exc_info:
                await provider.extract_recipe_from_text(SAMPLE_TEXT)

        assert "OpenAI API error" in str(exc_info.value)


class TestAnthropicProvider:
    """Tests for the Anthropic provider implementation."""

    @pytest.mark.asyncio
    async def test_extract_recipe_from_image_success(self):
        """Should successfully extract recipe from image using tool_use."""
        provider = AnthropicProvider(api_key="sk-ant-test")

        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "extract_recipe"
        mock_tool_block.input = SAMPLE_EXTRACTION_DATA

        mock_response = MagicMock()
        mock_response.content = [mock_tool_block]

        with patch.object(
            provider.client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.extract_recipe_from_image(
                SAMPLE_IMAGE_DATA, SAMPLE_MIME_TYPE
            )

        assert isinstance(result, RecipeExtraction)
        assert result.title == "Chocolate Chip Cookies"
        assert len(result.ingredients) == 3

    @pytest.mark.asyncio
    async def test_extract_recipe_from_text_success(self):
        """Should successfully extract recipe from text using tool_use."""
        provider = AnthropicProvider(api_key="sk-ant-test")

        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "extract_recipe"
        mock_tool_block.input = SAMPLE_EXTRACTION_DATA

        mock_response = MagicMock()
        mock_response.content = [mock_tool_block]

        with patch.object(
            provider.client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.extract_recipe_from_text(SAMPLE_TEXT)

        assert isinstance(result, RecipeExtraction)
        assert result.title == "Chocolate Chip Cookies"

    @pytest.mark.asyncio
    async def test_extract_recipe_raises_on_no_tool_response(self):
        """Should raise AIExtractionError when no tool_use in response."""
        provider = AnthropicProvider(api_key="sk-ant-test")

        mock_text_block = MagicMock()
        mock_text_block.type = "text"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        with patch.object(
            provider.client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(AIExtractionError) as exc_info:
                await provider.extract_recipe_from_text(SAMPLE_TEXT)

        assert "No tool use response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_recipe_raises_on_api_error(self):
        """Should raise AIExtractionError on API error."""
        provider = AnthropicProvider(api_key="sk-ant-test")

        with patch.object(
            provider.client.messages,
            "create",
            new_callable=AsyncMock,
            side_effect=Exception("Invalid API key"),
        ):
            with pytest.raises(AIExtractionError) as exc_info:
                await provider.extract_recipe_from_text(SAMPLE_TEXT)

        assert "Anthropic API error" in str(exc_info.value)


class TestGeminiProvider:
    """Tests for the Gemini provider implementation."""

    @pytest.mark.asyncio
    async def test_extract_recipe_from_image_success(self):
        """Should successfully extract recipe from image."""
        with patch("app.services.ai.gemini_provider.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = json.dumps(SAMPLE_EXTRACTION_DATA)
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="AIza-test")
            result = await provider.extract_recipe_from_image(
                SAMPLE_IMAGE_DATA, SAMPLE_MIME_TYPE
            )

        assert isinstance(result, RecipeExtraction)
        assert result.title == "Chocolate Chip Cookies"
        assert len(result.ingredients) == 3

    @pytest.mark.asyncio
    async def test_extract_recipe_from_text_success(self):
        """Should successfully extract recipe from text."""
        with patch("app.services.ai.gemini_provider.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = json.dumps(SAMPLE_EXTRACTION_DATA)
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="AIza-test")
            result = await provider.extract_recipe_from_text(SAMPLE_TEXT)

        assert isinstance(result, RecipeExtraction)
        assert result.title == "Chocolate Chip Cookies"

    @pytest.mark.asyncio
    async def test_extract_recipe_raises_on_empty_response(self):
        """Should raise AIExtractionError on empty response."""
        with patch("app.services.ai.gemini_provider.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = None
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="AIza-test")

            with pytest.raises(AIExtractionError) as exc_info:
                await provider.extract_recipe_from_text(SAMPLE_TEXT)

        assert "Empty response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_recipe_raises_on_api_error(self):
        """Should raise AIExtractionError on API error."""
        with patch("app.services.ai.gemini_provider.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(
                side_effect=Exception("Quota exceeded")
            )
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="AIza-test")

            with pytest.raises(AIExtractionError) as exc_info:
                await provider.extract_recipe_from_text(SAMPLE_TEXT)

        assert "Gemini API error" in str(exc_info.value)
