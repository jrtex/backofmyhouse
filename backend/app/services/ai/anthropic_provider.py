import base64
from typing import Any

from anthropic import AsyncAnthropic

from app.schemas.import_schemas import RecipeExtraction
from app.services.ai.base import AIProvider, AIExtractionError, with_retry
from app.services.ai.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_JSON_SCHEMA,
    IMAGE_USER_PROMPT,
    TEXT_USER_PROMPT_TEMPLATE,
)


class AnthropicProvider(AIProvider):
    """Anthropic-based recipe extraction."""

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

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

    async def extract_recipe_from_image(
        self, image_data: bytes, mime_type: str
    ) -> RecipeExtraction:
        """Extract recipe data from an image using Claude 3.5 Sonnet vision."""

        async def _extract() -> RecipeExtraction:
            base64_image = base64.b64encode(image_data).decode("utf-8")

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

            return self._parse_tool_response(response.content)

        try:
            return await with_retry(_extract)
        except AIExtractionError:
            raise
        except Exception as e:
            raise AIExtractionError(f"Anthropic API error: {e}")

    async def extract_recipe_from_text(self, text: str) -> RecipeExtraction:
        """Extract recipe data from text using Claude 3.5 Sonnet."""

        async def _extract() -> RecipeExtraction:
            user_prompt = TEXT_USER_PROMPT_TEMPLATE.format(text=text)

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=EXTRACTION_SYSTEM_PROMPT,
                tools=[self._get_extraction_tool()],
                tool_choice={"type": "tool", "name": "extract_recipe"},
                messages=[{"role": "user", "content": user_prompt}],
            )

            return self._parse_tool_response(response.content)

        try:
            return await with_retry(_extract)
        except AIExtractionError:
            raise
        except Exception as e:
            raise AIExtractionError(f"Anthropic API error: {e}")
