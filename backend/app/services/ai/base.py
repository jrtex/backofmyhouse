import asyncio
from abc import ABC, abstractmethod
from typing import Callable, TypeVar

from app.schemas.import_schemas import RecipeExtraction

T = TypeVar("T")


class AIProviderError(Exception):
    """Base exception for AI provider errors."""

    pass


class AINotConfiguredError(AIProviderError):
    """Raised when no AI provider is configured."""

    pass


class AIExtractionError(AIProviderError):
    """Raised when recipe extraction fails."""

    pass


class AITransientError(AIProviderError):
    """Raised for transient errors that should be retried."""

    pass


def is_transient_error(error: Exception) -> bool:
    """Check if an error is transient and should be retried.

    Args:
        error: The exception to check.

    Returns:
        True if the error is transient (network, timeout, 5xx), False otherwise.
    """
    error_str = str(error).lower()

    # Network and connection errors
    if any(
        term in error_str
        for term in ["connection", "timeout", "network", "temporary", "unavailable"]
    ):
        return True

    # HTTP 5xx server errors
    if any(code in error_str for code in ["500", "502", "503", "504"]):
        return True

    # Rate limiting (429) - could be transient
    if "429" in error_str or "rate limit" in error_str:
        return True

    return False


async def with_retry(
    operation: Callable[[], T],
    max_retries: int = 1,
    delay_seconds: float = 1.0,
) -> T:
    """Execute an async operation with retry on transient failures.

    Args:
        operation: Async callable to execute.
        max_retries: Maximum number of retry attempts (default: 1).
        delay_seconds: Delay between retries in seconds (default: 1.0).

    Returns:
        The result of the operation.

    Raises:
        AIExtractionError: If extraction fails.
        Exception: Re-raises non-transient exceptions for caller to handle.
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except AIExtractionError as e:
            # Check if the underlying error is transient
            if is_transient_error(e) and attempt < max_retries:
                last_error = e
                await asyncio.sleep(delay_seconds)
                continue
            raise
        except Exception as e:
            if is_transient_error(e) and attempt < max_retries:
                last_error = e
                await asyncio.sleep(delay_seconds)
                continue
            # Re-raise non-transient exceptions for caller to handle with
            # provider-specific error message
            raise

    # Should not reach here, but handle just in case
    raise AIExtractionError(f"All retry attempts failed: {last_error}")


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
