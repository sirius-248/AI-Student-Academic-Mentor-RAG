"""Data model for retrieved search context.

Encapsulates the user query, matched SearchResult objects, execution latency,
and top_k parameter.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.vector_store.search_result import SearchResult


@dataclass
class RetrievedContext:
    """Represents the structured context retrieved for a user query.

    Attributes:
        query: The input search query string.
        results: List of SearchResult objects containing matched DocumentChunks and similarity scores.
        retrieval_time_ms: Total retrieval execution time in milliseconds.
        top_k: Number of requested top results.
    """

    query: str
    results: List[SearchResult]
    retrieval_time_ms: float
    top_k: int
