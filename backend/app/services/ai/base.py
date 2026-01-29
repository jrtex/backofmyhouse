from abc import ABC, abstractmethod

from app.schemas.import_schemas import RecipeExtraction


class AIProviderError(Exception):
    """Base exception for AI provider errors."""

    pass


class AINotConfiguredError(AIProviderError):
    """Raised when no AI provider is configured."""

    pass


class AIExtractionError(AIProviderError):
    """Raised when recipe extraction fails."""

    pass


class AIProvider(ABC):
    """Abstract base class for AI providers.

    Each provider implementation must support extracting recipe data
    from both images and text content.
    """

    def __init__(self, api_key: str):
        """Initialize the provider with an API key.

        Args:
            api_key: The API key for authenticating with the provider.
        """
        self.api_key = api_key

    @abstractmethod
    async def extract_recipe_from_image(
        self, image_data: bytes, mime_type: str
    ) -> RecipeExtraction:
        """Extract recipe data from an image.

        Args:
            image_data: Raw image bytes.
            mime_type: MIME type of the image (e.g., 'image/jpeg', 'image/png').

        Returns:
            RecipeExtraction with extracted recipe data.

        Raises:
            AIExtractionError: If extraction fails.
        """
        pass

    @abstractmethod
    async def extract_recipe_from_text(self, text: str) -> RecipeExtraction:
        """Extract recipe data from text content.

        Args:
            text: Raw text containing recipe information.

        Returns:
            RecipeExtraction with extracted recipe data.

        Raises:
            AIExtractionError: If extraction fails.
        """
        pass
