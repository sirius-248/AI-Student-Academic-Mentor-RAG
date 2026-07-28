from __future__ import annotations

"""Skeleton OpenAI embedder.

This class defines the expected interface for an OpenAI-backed embedder but
intentionally does not implement API calls. Use this class as a blueprint for
future OpenAI integration.
"""
from typing import List
import logging

from .base_embedder import BaseEmbedder

logger = logging.getLogger(__name__)


class OpenAIEmbedder(BaseEmbedder):
    """Placeholder for OpenAI embeddings integration.

    Raises NotImplementedError for embed_text and embed_batch until a concrete
    implementation that performs API calls is provided.
    """

    def __init__(self, *args, **kwargs) -> None:
        logger.info("Initialized OpenAIEmbedder placeholder; not implemented")

    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError("OpenAIEmbedder is a placeholder and does not perform API calls yet.")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("OpenAIEmbedder is a placeholder and does not perform API calls yet.")
