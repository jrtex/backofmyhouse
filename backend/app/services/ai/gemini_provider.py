import json
import time

import google.generativeai as genai

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


class GeminiProvider(AIProvider):
    """Google Gemini-based recipe extraction."""

    DEFAULT_MODEL = "gemini-2.5-flash"
    provider_name = "gemini"

    def __init__(self, api_key: str, model: str | None = None):
        super().__init__(api_key)
        genai.configure(api_key=api_key)
        self.model_name = model or self.DEFAULT_MODEL
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
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

    def _build_result(self, response, extraction: RecipeExtraction, duration_ms: int) -> AIExtractionResult:
        """Build AIExtractionResult from Gemini response."""
        usage = getattr(response, "usage_metadata", None)
        return AIExtractionResult(
            extraction=extraction,
            provider="gemini",
            model=self.model_name,
            input_tokens=getattr(usage, "prompt_token_count", None) if usage else None,
            output_tokens=getattr(usage, "candidates_token_count", None) if usage else None,
            total_tokens=getattr(usage, "total_token_count", None) if usage else None,
            duration_ms=duration_ms,
        )

    async def extract_recipe_from_image(
        self, image_data: bytes, mime_type: str
    ) -> AIExtractionResult:
        """Extract recipe data from an image using Gemini vision."""

        async def _extract() -> AIExtractionResult:
            image_part = {
                "mime_type": mime_type,
                "data": image_data,
            }

            start = time.monotonic()
            response = await self.model.generate_content_async(
                [image_part, IMAGE_USER_PROMPT]
            )
            duration_ms = int((time.monotonic() - start) * 1000)

            if not response.text:
                raise AIExtractionError("Empty response from Gemini")

            extraction = self._parse_response(response.text)
            return self._build_result(response, extraction, duration_ms)

        try:
            return await with_retry(_extract)
        except AIExtractionError:
            raise
        except Exception as e:
            raise AIExtractionError(f"Gemini API error: {e}")

    async def extract_recipe_from_text(self, text: str) -> AIExtractionResult:
        """Extract recipe data from text using Gemini."""

        async def _extract() -> AIExtractionResult:
            user_prompt = TEXT_USER_PROMPT_TEMPLATE.format(text=text)

            start = time.monotonic()
            response = await self.model.generate_content_async(user_prompt)
            duration_ms = int((time.monotonic() - start) * 1000)

            if not response.text:
                raise AIExtractionError("Empty response from Gemini")

            extraction = self._parse_response(response.text)
            return self._build_result(response, extraction, duration_ms)

        try:
            return await with_retry(_extract)
        except AIExtractionError:
            raise
        except Exception as e:
            raise AIExtractionError(f"Gemini API error: {e}")

    async def extract_recipe_from_pdf(self, pdf_data: bytes) -> AIExtractionResult:
        """Extract recipe data from a PDF using Gemini's native PDF support."""

        async def _extract() -> AIExtractionResult:
            pdf_part = {
                "mime_type": "application/pdf",
                "data": pdf_data,
            }

            start = time.monotonic()
            response = await self.model.generate_content_async(
                [pdf_part, PDF_USER_PROMPT]
            )
            duration_ms = int((time.monotonic() - start) * 1000)

            if not response.text:
                raise AIExtractionError("Empty response from Gemini")

            extraction = self._parse_response(response.text)
            return self._build_result(response, extraction, duration_ms)

        try:
            return await with_retry(_extract)
        except AIExtractionError:
            raise
        except Exception as e:
            raise AIExtractionError(f"Gemini API error: {e}")
