from __future__ import annotations

"""Base embedder abstraction and embedding-specific exceptions.

Defines the contract every embedder must follow. Keeps backward-compatible
names for previously exported exceptions while introducing a clearer
exception hierarchy.
"""
from abc import ABC, abstractmethod
from typing import Sequence, List
import logging

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Base exception for embedding-related errors."""


class EmbeddingInitializationError(EmbeddingError):
    """Raised when an embedder fails to initialize (e.g., missing dependency or model load error)."""


class EmbeddingValidationError(EmbeddingError):
    """Raised when invalid inputs are provided to an embedder (e.g., None batch)."""


class EmbeddingGenerationError(EmbeddingError):
    """Raised when an error occurs during embedding generation (runtime)."""


# Backwards compatibility aliases (existing code may import these names)
EmbedderError = EmbeddingError
EmbedderInitializationError = EmbeddingInitializationError


class BaseEmbedder(ABC):
    """Abstract base class for all embedders.

    Concrete embedders must implement embed_text and embed_batch. Both methods
    return embeddings as nested Python lists of floats.
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string.

        Args:
            text: Input text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        raise NotImplementedError

    @abstractmethod
    def embed_batch(self, texts: Sequence[str]) -> List[List[float]]:
        """Embed a batch of text strings.

        Args:
            texts: Sequence of input strings. The output list MUST preserve input order
                   such that embeddings[i] corresponds to texts[i].

        Returns:
            A list of embedding vectors (each vector is a list of floats).
        """
        raise NotImplementedError
