import base64
import time
from typing import Any

from anthropic import AsyncAnthropic

from app.schemas.import_schemas import RecipeExtraction
from app.services.ai.base import AIProvider, AIExtractionError, with_retry
from app.services.ai.result import AIExtractionResult
from app.services.ai.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_JSON_SCHEMA,
    IMAGE_USER_PROMPT,
    TEXT_USER_PROMPT_TEMPLATE,
    PDF_USER_PROMPT,
)


class AnthropicProvider(AIProvider):
    """Anthropic-based recipe extraction."""

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    provider_name = "anthropic"

    def __init__(self, api_key: str, model: str | None = None):
        super().__init__(api_key)
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model or self.DEFAULT_MODEL

    def _get_extraction_tool(self) -> dict[str, Any]:
        """Get the tool definition for structured recipe extraction."""
        return {
            "name": "extract_recipe",
            "description": "Extract structured recipe data from the content",
            "input_schema": EXTRACTION_JSON_SCHEMA,
        }

    def _parse_tool_response(self, content: list) -> RecipeExtraction:
        """Parse the tool use response into a RecipeExtraction object."""
        for block in content:
            if block.type == "tool_use" and block.name == "extract_recipe":
                try:
                    return RecipeExtraction(**block.input)
                except Exception as e:
                    raise AIExtractionError(f"Failed to create RecipeExtraction: {e}")

        raise AIExtractionError("No tool use response found in API response")

    def _build_result(self, response, extraction: RecipeExtraction, duration_ms: int) -> AIExtractionResult:
        """Build AIExtractionResult from Anthropic response."""
        usage = response.usage
        return AIExtractionResult(
            extraction=extraction,
            provider="anthropic",
            model=self.model,
            input_tokens=usage.input_tokens if usage else None,
            output_tokens=usage.output_tokens if usage else None,
            total_tokens=(usage.input_tokens + usage.output_tokens) if usage else None,
            duration_ms=duration_ms,
        )

    async def extract_recipe_from_image(
        self, image_data: bytes, mime_type: str
    ) -> AIExtractionResult:
        """Extract recipe data from an image using Claude vision."""

        async def _extract() -> AIExtractionResult:
            base64_image = base64.b64encode(image_data).decode("utf-8")

            start = time.monotonic()
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=EXTRACTION_SYSTEM_PROMPT,
                tools=[self._get_extraction_tool()],
                tool_choice={"type": "tool", "name": "extract_recipe"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": base64_image,
                                },
                            },
                            {"type": "text", "text": IMAGE_USER_PROMPT},
                        ],
                    }
                ],
            )
            duration_ms = int((time.monotonic() - start) * 1000)

            extraction = self._parse_tool_response(response.content)
            return self._build_result(response, extraction, duration_ms)

        try:
            return await with_retry(_extract)
        except AIExtractionError:
            raise
        except Exception as e:
            raise AIExtractionError(f"Anthropic API error: {e}")

    async def extract_recipe_from_text(self, text: str) -> AIExtractionResult:
        """Extract recipe data from text using Claude."""

        async def _extract() -> AIExtractionResult:
            user_prompt = TEXT_USER_PROMPT_TEMPLATE.format(text=text)

            start = time.monotonic()
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=EXTRACTION_SYSTEM_PROMPT,
                tools=[self._get_extraction_tool()],
                tool_choice={"type": "tool", "name": "extract_recipe"},
                messages=[{"role": "user", "content": user_prompt}],
            )
            duration_ms = int((time.monotonic() - start) * 1000)

            extraction = self._parse_tool_response(response.content)
            return self._build_result(response, extraction, duration_ms)

        try:
            return await with_retry(_extract)
        except AIExtractionError:
            raise
        except Exception as e:
            raise AIExtractionError(f"Anthropic API error: {e}")

    async def extract_recipe_from_pdf(self, pdf_data: bytes) -> AIExtractionResult:
        """Extract recipe data from a PDF using Claude's native PDF support."""

        async def _extract() -> AIExtractionResult:
            pdf_base64 = base64.standard_b64encode(pdf_data).decode("utf-8")

            start = time.monotonic()
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=EXTRACTION_SYSTEM_PROMPT,
                tools=[self._get_extraction_tool()],
                tool_choice={"type": "tool", "name": "extract_recipe"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_base64,
                                },
                            },
                            {"type": "text", "text": PDF_USER_PROMPT},
                        ],
                    }
                ],
            )
            duration_ms = int((time.monotonic() - start) * 1000)

            extraction = self._parse_tool_response(response.content)
            return self._build_result(response, extraction, duration_ms)

        try:
            return await with_retry(_extract)
        except AIExtractionError:
            raise
        except Exception as e:
            raise AIExtractionError(f"Anthropic API error: {e}")
