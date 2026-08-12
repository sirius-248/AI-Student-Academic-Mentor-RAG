"""Utilities for embedding DocumentChunk objects.

Provides backward-compatible helper functions for embedding DocumentChunk collections.
Under the hood, delegates to EmbeddingService.
"""
from __future__ import annotations

from typing import List, Sequence, Optional
import logging

from .base_embedder import BaseEmbedder
from .embedding_service import EmbeddingService
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)


def embed_document_chunks(
    chunks: Sequence[DocumentChunk],
    embedder: Optional[BaseEmbedder] = None,
) -> List[DocumentChunk]:
    """Embed a list of DocumentChunk objects using EmbeddingService.

    Backward-compatible wrapper around EmbeddingService.embed_chunks.

    Args:
        chunks: Sequence of DocumentChunk instances.
        embedder: Optional instance of BaseEmbedder. If None, the default embedder is used.

    Returns:
        List of DocumentChunk objects with populated embedding fields.
    """
    service = EmbeddingService(embedder=embedder)
    return service.embed_chunks(chunks)

