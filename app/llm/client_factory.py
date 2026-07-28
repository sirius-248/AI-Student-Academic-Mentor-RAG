"""Factory for selecting the LLM client implementation."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from .base_client import BaseLLMClient, LLMClientError
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class LLMClientFactory:
    """Factory class for creating LLM clients based on environment configuration."""

    @staticmethod
    def create_client() -> BaseLLMClient:
        project_root = Path(__file__).resolve().parents[2]
        dotenv_path = project_root / ".env"
        load_dotenv(dotenv_path=dotenv_path)

        provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        if provider == "gemini":
            return GeminiClient()
        if provider == "openai":
            return OpenAIClient()
        if provider == "azure":
            raise NotImplementedError(
                "Azure OpenAI integration will be added in the next milestone."
            )

        raise LLMClientError(
            f"Unsupported LLM_PROVIDER '{provider}'. Supported values: gemini, openai, azure."
        )
