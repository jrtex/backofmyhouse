import base64
import json
from typing import Any

from openai import AsyncOpenAI

from app.schemas.import_schemas import RecipeExtraction
from app.services.ai.base import AIProvider, AIExtractionError, with_retry
from app.services.ai.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_JSON_SCHEMA,
    IMAGE_USER_PROMPT,
    TEXT_USER_PROMPT_TEMPLATE,
)


class OpenAIProvider(AIProvider):
    """OpenAI-based recipe extraction."""

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, api_key: str, model: str | None = None):
        super().__init__(api_key)
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model or self.DEFAULT_MODEL

    def _build_system_message(self) -> dict[str, Any]:
        """Build system message with extraction instructions and schema."""
        schema_instruction = (
            f"\n\nYou must respond with valid JSON matching this schema:\n"
            f"{json.dumps(EXTRACTION_JSON_SCHEMA, indent=2)}"
        )
        return {
            "role": "system",
            "content": EXTRACTION_SYSTEM_PROMPT + schema_instruction,
        }

    def _parse_response(self, content: str) -> RecipeExtraction:
        """Parse the model response into a RecipeExtraction object."""
        try:
            data = json.loads(content)
            return RecipeExtraction(**data)
        except json.JSONDecodeError as e:
            raise AIExtractionError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise AIExtractionError(f"Failed to create RecipeExtraction: {e}")

    async def extract_recipe_from_image(
        self, image_data: bytes, mime_type: str
    ) -> RecipeExtraction:
        """Extract recipe data from an image using GPT-4o-mini vision."""

        async def _extract() -> RecipeExtraction:
            base64_image = base64.b64encode(image_data).decode("utf-8")
            data_url = f"data:{mime_type};base64,{base64_image}"

            response = await self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    self._build_system_message(),
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": IMAGE_USER_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url},
                            },
                        ],
                    },
                ],
                max_tokens=4096,
            )

            content = response.choices[0].message.content
            if not content:
                raise AIExtractionError("Empty response from OpenAI")

            return self._parse_response(content)

        try:
            return await with_retry(_extract)
        except AIExtractionError:
            raise
        except Exception as e:
            raise AIExtractionError(f"OpenAI API error: {e}")

    async def extract_recipe_from_text(self, text: str) -> RecipeExtraction:
        """Extract recipe data from text using GPT-4o-mini."""

        async def _extract() -> RecipeExtraction:
            user_prompt = TEXT_USER_PROMPT_TEMPLATE.format(text=text)

            response = await self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    self._build_system_message(),
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=4096,
            )

            content = response.choices[0].message.content
            if not content:
                raise AIExtractionError("Empty response from OpenAI")

            return self._parse_response(content)

        try:
            return await with_retry(_extract)
        except AIExtractionError:
            raise
        except Exception as e:
            raise AIExtractionError(f"OpenAI API error: {e}")
