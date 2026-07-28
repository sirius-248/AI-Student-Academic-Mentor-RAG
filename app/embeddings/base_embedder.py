from __future__ import annotations

"""Base embedder abstraction and common exceptions.

Defines the contract every embedder must follow.
"""
from abc import ABC, abstractmethod
from typing import List
import logging

logger = logging.getLogger(__name__)


class EmbedderError(Exception):
    """Base exception for embedder-related errors."""


class EmbedderInitializationError(EmbedderError):
    """Raised when an embedder fails to initialize (e.g., missing dependency or model load error)."""


class BaseEmbedder(ABC):
    """Abstract base class for all embedders.

    Concrete embedders must implement embed_text and embed_batch. Both methods
    return embeddings as nested Python lists of floats (list[float] or list[list[float]]).
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
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings.

        Args:
            texts: List of input strings. The output list MUST preserve input order
                   such that embeddings[i] corresponds to texts[i].

        Returns:
            A list of embedding vectors (each vector is a list of floats).
        """
        raise NotImplementedError
