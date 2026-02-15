import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.import_schemas import RecipeExtraction
from app.services.ai import (
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    AIExtractionError,
    PDFNotSupportedError,
    AIExtractionResult,
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
SAMPLE_PDF_DATA = b"%PDF-1.4 fake pdf content"


def _mock_openai_usage():
    usage = MagicMock()
    usage.prompt_tokens = 500
    usage.completion_tokens = 300
    usage.total_tokens = 800
    return usage


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
        mock_response.usage = _mock_openai_usage()

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.extract_recipe_from_image(
                SAMPLE_IMAGE_DATA, SAMPLE_MIME_TYPE
            )

        assert isinstance(result, AIExtractionResult)
        assert result.extraction.title == "Chocolate Chip Cookies"
        assert len(result.extraction.ingredients) == 3
        assert len(result.extraction.instructions) == 3
        assert result.extraction.confidence == 0.95
        assert result.provider == "openai"
        assert result.input_tokens == 500
        assert result.output_tokens == 300
        assert result.total_tokens == 800
        assert result.duration_ms is not None

    @pytest.mark.asyncio
    async def test_extract_recipe_from_text_success(self):
        """Should successfully extract recipe from text."""
        provider = OpenAIProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(SAMPLE_EXTRACTION_DATA)))
        ]
        mock_response.usage = _mock_openai_usage()

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.extract_recipe_from_text(SAMPLE_TEXT)

        assert isinstance(result, AIExtractionResult)
        assert result.extraction.title == "Chocolate Chip Cookies"
        assert result.provider == "openai"
        assert result.input_tokens == 500

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

    @pytest.mark.asyncio
    async def test_extract_recipe_from_pdf_raises_not_supported(self):
        """Should raise PDFNotSupportedError for PDF extraction."""
        provider = OpenAIProvider(api_key="sk-test")

        with pytest.raises(PDFNotSupportedError) as exc_info:
            await provider.extract_recipe_from_pdf(SAMPLE_PDF_DATA)

        assert "not supported with OpenAI" in str(exc_info.value)
        assert "Anthropic or Gemini" in str(exc_info.value)

    def test_provider_name(self):
        provider = OpenAIProvider(api_key="sk-test")
        assert provider.provider_name == "openai"


def _mock_anthropic_usage():
    usage = MagicMock()
    usage.input_tokens = 400
    usage.output_tokens = 250
    return usage


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
        mock_response.usage = _mock_anthropic_usage()

        with patch.object(
            provider.client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.extract_recipe_from_image(
                SAMPLE_IMAGE_DATA, SAMPLE_MIME_TYPE
            )

        assert isinstance(result, AIExtractionResult)
        assert result.extraction.title == "Chocolate Chip Cookies"
        assert len(result.extraction.ingredients) == 3
        assert result.provider == "anthropic"
        assert result.input_tokens == 400
        assert result.output_tokens == 250
        assert result.total_tokens == 650
        assert result.duration_ms is not None

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
        mock_response.usage = _mock_anthropic_usage()

        with patch.object(
            provider.client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.extract_recipe_from_text(SAMPLE_TEXT)

        assert isinstance(result, AIExtractionResult)
        assert result.extraction.title == "Chocolate Chip Cookies"
        assert result.provider == "anthropic"

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

    @pytest.mark.asyncio
    async def test_extract_recipe_from_pdf_success(self):
        """Should successfully extract recipe from PDF using document type."""
        provider = AnthropicProvider(api_key="sk-ant-test")

        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "extract_recipe"
        mock_tool_block.input = SAMPLE_EXTRACTION_DATA

        mock_response = MagicMock()
        mock_response.content = [mock_tool_block]
        mock_response.usage = _mock_anthropic_usage()

        with patch.object(
            provider.client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_create:
            result = await provider.extract_recipe_from_pdf(SAMPLE_PDF_DATA)

        assert isinstance(result, AIExtractionResult)
        assert result.extraction.title == "Chocolate Chip Cookies"
        assert result.provider == "anthropic"

        # Verify the API was called with document type for PDF
        call_args = mock_create.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["content"][0]["type"] == "document"
        assert messages[0]["content"][0]["source"]["media_type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_extract_recipe_from_pdf_raises_on_api_error(self):
        """Should raise AIExtractionError on PDF API error."""
        provider = AnthropicProvider(api_key="sk-ant-test")

        with patch.object(
            provider.client.messages,
            "create",
            new_callable=AsyncMock,
            side_effect=Exception("PDF processing failed"),
        ):
            with pytest.raises(AIExtractionError) as exc_info:
                await provider.extract_recipe_from_pdf(SAMPLE_PDF_DATA)

        assert "Anthropic API error" in str(exc_info.value)

    def test_provider_name(self):
        provider = AnthropicProvider(api_key="sk-ant-test")
        assert provider.provider_name == "anthropic"


class TestGeminiProvider:
    """Tests for the Gemini provider implementation."""

    def _mock_gemini_usage(self):
        usage = MagicMock()
        usage.prompt_token_count = 350
        usage.candidates_token_count = 200
        usage.total_token_count = 550
        return usage

    @pytest.mark.asyncio
    async def test_extract_recipe_from_image_success(self):
        """Should successfully extract recipe from image."""
        with patch("app.services.ai.gemini_provider.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = json.dumps(SAMPLE_EXTRACTION_DATA)
            mock_response.usage_metadata = self._mock_gemini_usage()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="AIza-test")
            result = await provider.extract_recipe_from_image(
                SAMPLE_IMAGE_DATA, SAMPLE_MIME_TYPE
            )

        assert isinstance(result, AIExtractionResult)
        assert result.extraction.title == "Chocolate Chip Cookies"
        assert len(result.extraction.ingredients) == 3
        assert result.provider == "gemini"
        assert result.input_tokens == 350
        assert result.output_tokens == 200
        assert result.total_tokens == 550
        assert result.duration_ms is not None

    @pytest.mark.asyncio
    async def test_extract_recipe_from_text_success(self):
        """Should successfully extract recipe from text."""
        with patch("app.services.ai.gemini_provider.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = json.dumps(SAMPLE_EXTRACTION_DATA)
            mock_response.usage_metadata = self._mock_gemini_usage()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="AIza-test")
            result = await provider.extract_recipe_from_text(SAMPLE_TEXT)

        assert isinstance(result, AIExtractionResult)
        assert result.extraction.title == "Chocolate Chip Cookies"
        assert result.provider == "gemini"

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

    @pytest.mark.asyncio
    async def test_extract_recipe_from_pdf_success(self):
        """Should successfully extract recipe from PDF."""
        with patch("app.services.ai.gemini_provider.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = json.dumps(SAMPLE_EXTRACTION_DATA)
            mock_response.usage_metadata = self._mock_gemini_usage()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="AIza-test")
            result = await provider.extract_recipe_from_pdf(SAMPLE_PDF_DATA)

        assert isinstance(result, AIExtractionResult)
        assert result.extraction.title == "Chocolate Chip Cookies"
        assert len(result.extraction.ingredients) == 3
        assert result.provider == "gemini"

        # Verify the API was called with PDF data
        call_args = mock_model.generate_content_async.call_args
        content_parts = call_args[0][0]
        assert content_parts[0]["mime_type"] == "application/pdf"
        assert content_parts[0]["data"] == SAMPLE_PDF_DATA

    @pytest.mark.asyncio
    async def test_extract_recipe_from_pdf_raises_on_empty_response(self):
        """Should raise AIExtractionError on empty PDF response."""
        with patch("app.services.ai.gemini_provider.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = None
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="AIza-test")

            with pytest.raises(AIExtractionError) as exc_info:
                await provider.extract_recipe_from_pdf(SAMPLE_PDF_DATA)

        assert "Empty response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_recipe_from_pdf_raises_on_api_error(self):
        """Should raise AIExtractionError on PDF API error."""
        with patch("app.services.ai.gemini_provider.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(
                side_effect=Exception("PDF processing error")
            )
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="AIza-test")

            with pytest.raises(AIExtractionError) as exc_info:
                await provider.extract_recipe_from_pdf(SAMPLE_PDF_DATA)

        assert "Gemini API error" in str(exc_info.value)

    def test_provider_name(self):
        with patch("app.services.ai.gemini_provider.genai"):
            provider = GeminiProvider(api_key="AIza-test")
        assert provider.provider_name == "gemini"
