"""Factory for constructing vector store instances by provider key.

Decouples application code from concrete vector database implementations.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_vector_store import BaseVectorStore
from .faiss_vector_store import FAISSVectorStore
from .config import VECTOR_STORE_PROVIDER
from .exceptions import (
    VectorStoreInitializationError,
    VectorStoreValidationError,
)

logger = logging.getLogger(__name__)


class VectorStoreFactory:
    """Factory class for instantiating vector store providers.

    Supported provider keys (case-insensitive):
        - "faiss"

    Example:
        store = VectorStoreFactory.get_vector_store("faiss")
    """

    _providers = {
        "faiss": FAISSVectorStore,
    }

    @classmethod
    def get_vector_store(
        cls,
        provider: str = VECTOR_STORE_PROVIDER,
        **kwargs: Any,
    ) -> BaseVectorStore:
        """Return a vector store instance for the requested provider.

        Args:
            provider: Provider key string (case-insensitive). Defaults to VECTOR_STORE_PROVIDER from config.
            **kwargs: Additional keyword arguments passed to the provider constructor.

        Returns:
            An instance of BaseVectorStore.

        Raises:
            VectorStoreValidationError: If provider is not a non-empty string.
            VectorStoreInitializationError: If provider key is unknown.
        """
        if not provider or not isinstance(provider, str):
            raise VectorStoreValidationError("provider must be a non-empty string")

        key = provider.strip().lower()
        provider_cls = cls._providers.get(key)
        if provider_cls is None:
            valid = ", ".join(sorted(cls._providers.keys()))
            raise VectorStoreInitializationError(
                f"Unknown vector store provider '{provider}'. Valid providers: {valid}"
            )

        logger.info("Creating vector store for provider '%s'", key)
        return provider_cls(**kwargs)
