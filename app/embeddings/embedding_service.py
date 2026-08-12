"""Embedding service orchestration layer.

Provides a unified interface for embedding DocumentChunk collections using any
BaseEmbedder strategy. Encapsulates text extraction, batch vector generation,
vector assignment, and logging.
"""
from __future__ import annotations

from typing import List, Sequence, Optional
import logging
import time

from .base_embedder import BaseEmbedder, EmbeddingValidationError
from .embedder_factory import EmbedderFactory
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Orchestration service for generating embeddings for DocumentChunk objects.

    Attributes:
        embedder: The concrete BaseEmbedder instance used to generate vectors.
    """

    def __init__(self, embedder: Optional[BaseEmbedder] = None) -> None:
        """Initialize EmbeddingService.

        Args:
            embedder: An instance of BaseEmbedder. If None, the default embedder
                     is created via EmbedderFactory.
        """
        if embedder is None:
            logger.info("No embedder provided to EmbeddingService; constructing default embedder via EmbedderFactory")
            self.embedder = EmbedderFactory.get_embedder()
        else:
            self.embedder = embedder

    def embed_chunks(self, chunks: Sequence[DocumentChunk]) -> List[DocumentChunk]:
        """Embed a collection of DocumentChunk objects and assign vectors in-place.

        Args:
            chunks: A sequence of DocumentChunk instances.

        Returns:
            The list of DocumentChunk objects with updated .embedding attributes.

        Raises:
            EmbeddingValidationError: If chunks is None or not an iterable collection.
        """
        if chunks is None:
            raise EmbeddingValidationError("chunks must be a sequence of DocumentChunk instances (got None)")

        # Convert to list to preserve deterministic order and allow indexing
        try:
            chunk_list = list(chunks)
        except TypeError as exc:
            raise EmbeddingValidationError("chunks must be an iterable sequence of DocumentChunk instances") from exc

        if not chunk_list:
            logger.info("embed_chunks called with an empty collection of DocumentChunk objects")
            return []

        # Extract texts safely
        texts: List[str] = []
        for i, chunk in enumerate(chunk_list):
            if chunk is None:
                logger.warning("Chunk at index %d is None; treating as empty string", i)
                texts.append("")
            else:
                chunk_text = getattr(chunk, "text", "")
                if chunk_text is None:
                    logger.warning("Chunk %s has None text at index %d; treating as empty string", getattr(chunk, "chunk_id", i), i)
                    texts.append("")
                else:
                    texts.append(str(chunk_text))

        logger.info("EmbeddingService processing %d DocumentChunk objects using %s", len(chunk_list), type(self.embedder).__name__)
        start_time = time.time()

        embeddings = self.embedder.embed_batch(texts)

        if embeddings is None:
            raise EmbeddingValidationError("Embedder embed_batch returned None")

        if len(embeddings) != len(chunk_list):
            logger.warning(
                "Embedder returned %d embeddings for %d input chunks; assigning up to min length",
                len(embeddings),
                len(chunk_list),
            )

        # Assign vectors back to DocumentChunk objects
        assigned_count = 0
        for i, chunk in enumerate(chunk_list):
            if i < len(embeddings):
                if chunk is not None:
                    chunk.embedding = embeddings[i]
                    assigned_count += 1
            else:
                logger.warning("No embedding vector returned for chunk at index %d", i)

        elapsed = time.time() - start_time
        if embeddings and len(embeddings) > 0:
            dimension = len(embeddings[0])
            logger.debug("Successfully assigned %d vectors of dimension %d", assigned_count, dimension)

        logger.info("Successfully completed embedding %d DocumentChunk objects in %.3fs", assigned_count, elapsed)
        return chunk_list

    def embed_query(self, query: str) -> List[float]:
        """Generate an embedding vector for a single query string.

        Args:
            query: The search query string.

        Returns:
            List of float values representing the query embedding vector.

        Raises:
            EmbeddingValidationError: If query is None, not a string, or empty.
        """
        if query is None or not isinstance(query, str) or not query.strip():
            raise EmbeddingValidationError("query must be a non-empty string")

        logger.debug("EmbeddingService generating query vector for text length %d", len(query))
        return self.embedder.embed_text(query.strip())

