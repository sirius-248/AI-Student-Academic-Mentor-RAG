"""Data model for vector search results.

Wraps a matched DocumentChunk alongside its similarity score.
"""
from __future__ import annotations

from dataclasses import dataclass
from app.models.document_chunk import DocumentChunk


@dataclass
class SearchResult:
    """Represents a search result returned from the vector store.

    Attributes:
        chunk: The matched DocumentChunk object.
        score: The similarity score (cosine similarity for normalized vectors).
    """

    chunk: DocumentChunk
    score: float
