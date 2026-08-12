from __future__ import annotations

"""Factory for constructing embedder instances by provider name.

Consumers should use EmbedderFactory.get_embedder(...) rather than
instantiating provider classes directly. This keeps the rest of the application
decoupled from concrete embedding implementations.
"""
from typing import Any
import logging

from .sentence_transformer_embedder import SentenceTransformerEmbedder
from .openai_embedder import OpenAIEmbedder
from .gemini_embedder import GeminiEmbedder
from .base_embedder import (
    BaseEmbedder,
    EmbeddingValidationError,
    EmbeddingInitializationError,
)
from .config import DEFAULT_PROVIDER

logger = logging.getLogger(__name__)


class EmbedderFactory:
    """Create embedder instances by provider key.

    Supported provider keys (case-insensitive):
      - "sentence_transformer"
      - "openai"
      - "gemini"

    Example:
        embedder = EmbedderFactory.get_embedder("sentence_transformer", model_name="BAAI/bge-small-en-v1.5")
    """

    _providers = {
        "sentence_transformer": SentenceTransformerEmbedder,
        "openai": OpenAIEmbedder,
        "gemini": GeminiEmbedder,
    }

    @classmethod
    def get_embedder(cls, provider: str = DEFAULT_PROVIDER, **kwargs: Any) -> BaseEmbedder:
        """Return an embedder instance for the requested provider.

        Args:
            provider: Provider key (case-insensitive). Valid values listed above.
                      Defaults to DEFAULT_PROVIDER from config.
            **kwargs: Forwarded to the provider's constructor (e.g., model_name, device).

        Returns:
            An instance of BaseEmbedder.

        Raises:
            EmbeddingValidationError: If provider is empty or not a string.
            EmbeddingInitializationError: If the provider key is unknown.
        """
        if not provider or not isinstance(provider, str):
            raise EmbeddingValidationError("provider must be a non-empty string")

        key = provider.strip().lower()
        provider_cls = cls._providers.get(key)
        if provider_cls is None:
            valid = ", ".join(sorted(cls._providers.keys()))
            raise EmbeddingInitializationError(f"Unknown embedder provider '{provider}'. Valid providers: {valid}")

        logger.info("Creating embedder for provider '%s'", key)
        return provider_cls(**kwargs)

