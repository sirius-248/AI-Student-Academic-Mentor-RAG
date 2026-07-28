"""Gemini LLM client implementation for the AI Academic Mentor."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from .base_client import BaseLLMClient, LLMClientError

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Client wrapper for Google Gemini using the google-genai v2.x SDK."""

    def __init__(self) -> None:
        """Initialize the Gemini client with API key and model from environment."""
        project_root = Path(__file__).resolve().parents[2]
        dotenv_path = project_root / ".env"
        load_dotenv(dotenv_path=dotenv_path, override=True)

        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise LLMClientError("Missing GEMINI_API_KEY environment variable.")

        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        logger.info(f"Initialized Gemini client with model: {self.model}")
        self.client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str) -> str:
        """Generate text from Gemini for the provided prompt.

        Args:
            prompt: The input prompt string.

        Returns:
            The generated text response.

        Raises:
            LLMClientError: If the generation fails or returns empty response.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt text must not be empty.")

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )

            if not response or not response.text:
                raise LLMClientError("Gemini returned an empty response.")

            return response.text
        except LLMClientError:
            raise
        except Exception as exc:
            logger.exception("Error generating content from Gemini.")
            raise LLMClientError(
                f"Failed to generate content from Gemini: {str(exc)}"
            ) from exc
