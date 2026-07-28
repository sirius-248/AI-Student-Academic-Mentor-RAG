"""Utilities for embedding DocumentChunk objects.

Contains helper functions that are provider-agnostic and operate on the
project's DocumentChunk dataclass.
"""
from __future__ import annotations

from typing import List
import logging

from .base_embedder import BaseEmbedder
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)


def embed_document_chunks(chunks: List[DocumentChunk], embedder: BaseEmbedder) -> List[DocumentChunk]:
    """Embed a list of DocumentChunk objects using the provided embedder.

    This function is provider-agnostic and relies only on the BaseEmbedder
    interface. It uses embed_batch for efficient processing and writes the
    resulting vectors back into each chunk.embedding field in-place.

    Args:
        chunks: List of DocumentChunk instances. The original list order is
                preserved and embeddings will be assigned in the same order.
        embedder: An instance of BaseEmbedder which performs the actual
                 embedding work (in-process or via API).

    Returns:
        The same list of DocumentChunk objects with their .embedding fields
        populated (or updated). The function returns the list for convenience.

    Raises:
        ValueError: If chunks is None or not an iterable of DocumentChunk.
        Any exceptions raised by the provided embedder are propagated after
        logging.
    """
    if chunks is None:
        raise ValueError("chunks must be a list of DocumentChunk instances (got None)")

    # Defensive: ensure list so we can index and preserve order
    chunk_list = list(chunks)

    # Extract texts, converting None to empty string to preserve alignment.
    texts: List[str] = []
    for i, ch in enumerate(chunk_list):
        if ch is None:
            logger.debug("Chunk at position %d is None; treating as empty text", i)
            texts.append("")
        else:
            # Access text, guard against None
            t = ch.text if getattr(ch, "text", None) is not None else ""
            texts.append(t)

    logger.info("Embedding %d DocumentChunk objects using embedder %s", len(texts), type(embedder).__name__)

    try:
        embeddings = embedder.embed_batch(texts)
    except Exception as exc:
        logger.exception("Embedding failed: %s", exc)
        raise

    if embeddings is None:
        raise ValueError("embedder.embed_batch returned None")

    if len(embeddings) != len(chunk_list):
        logger.warning(
            "embedder.embed_batch returned %d embeddings for %d inputs; truncating or padding as needed",
            len(embeddings),
            len(chunk_list),
        )

    # Assign embeddings back to chunks (preserve input order). If there are
    # fewer embeddings than inputs, remaining chunks retain their previous
    # embedding value; if there are more, extra embeddings are ignored.
    for i, ch in enumerate(chunk_list):
        if i < len(embeddings):
            ch.embedding = embeddings[i]
        else:
            logger.debug("No embedding available for chunk at index %d; leaving existing embedding unchanged", i)

    logger.info("Assigned embeddings to %d DocumentChunk objects", min(len(embeddings), len(chunk_list)))
    return chunk_list
