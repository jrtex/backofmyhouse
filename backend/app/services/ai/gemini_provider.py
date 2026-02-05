import json

import google.generativeai as genai

from app.schemas.import_schemas import RecipeExtraction
from app.services.ai.base import AIProvider, AIExtractionError, with_retry
from app.services.ai.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_JSON_SCHEMA,
    IMAGE_USER_PROMPT,
    TEXT_USER_PROMPT_TEMPLATE,
)


class GeminiProvider(AIProvider):
    """Google Gemini-based recipe extraction using Gemini 1.5 Flash."""

    MODEL = "gemini-1.5-flash"

    def __init__(self, api_key: str):
        super().__init__(api_key)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=self.MODEL,
            system_instruction=self._build_system_instruction(),
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=self._build_response_schema(),
            ),
        )

    def _build_system_instruction(self) -> str:
        """Build system instruction with extraction guidelines."""
        return EXTRACTION_SYSTEM_PROMPT

    def _build_response_schema(self) -> dict:
        """Build Gemini-compatible response schema.

        Gemini uses a slightly different schema format than JSON Schema.
        """
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "ingredients": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "quantity": {"type": "string"},
                            "unit": {"type": "string"},
                            "notes": {"type": "string"},
                        },
                        "required": ["name"],
                    },
                },
                "instructions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step_number": {"type": "integer"},
                            "text": {"type": "string"},
                        },
                        "required": ["step_number", "text"],
                    },
                },
                "prep_time_minutes": {"type": "integer"},
                "cook_time_minutes": {"type": "integer"},
                "servings": {"type": "integer"},
                "notes": {"type": "string"},
                "special_equipment": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "confidence": {"type": "number"},
                "warnings": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["title", "ingredients", "instructions", "confidence", "warnings"],
        }

    def _parse_response(self, text: str) -> RecipeExtraction:
        """Parse the model response into a RecipeExtraction object."""
        try:
            data = json.loads(text)
            return RecipeExtraction(**data)
        except json.JSONDecodeError as e:
            raise AIExtractionError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise AIExtractionError(f"Failed to create RecipeExtraction: {e}")

    async def extract_recipe_from_image(
        self, image_data: bytes, mime_type: str
    ) -> RecipeExtraction:
        """Extract recipe data from an image using Gemini 1.5 Flash vision."""

        async def _extract() -> RecipeExtraction:
            image_part = {
                "mime_type": mime_type,
                "data": image_data,
            }

            response = await self.model.generate_content_async(
                [image_part, IMAGE_USER_PROMPT]
            )

            if not response.text:
                raise AIExtractionError("Empty response from Gemini")

            return self._parse_response(response.text)

        try:
            return await with_retry(_extract)
        except AIExtractionError:
            raise
        except Exception as e:
            raise AIExtractionError(f"Gemini API error: {e}")

    async def extract_recipe_from_text(self, text: str) -> RecipeExtraction:
        """Extract recipe data from text using Gemini 1.5 Flash."""

        async def _extract() -> RecipeExtraction:
            user_prompt = TEXT_USER_PROMPT_TEMPLATE.format(text=text)

            response = await self.model.generate_content_async(user_prompt)

            if not response.text:
                raise AIExtractionError("Empty response from Gemini")

            return self._parse_response(response.text)

        try:
            return await with_retry(_extract)
        except AIExtractionError:
            raise
        except Exception as e:
            raise AIExtractionError(f"Gemini API error: {e}")
