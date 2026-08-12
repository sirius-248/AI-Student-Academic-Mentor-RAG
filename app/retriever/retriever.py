"""Retriever orchestration layer.

Connects user queries with EmbeddingService and BaseVectorStore to perform
semantic retrieval, apply similarity filtering, and measure execution latency.
"""
from __future__ import annotations

import logging
import time
from typing import Optional, List

from app.embeddings.embedding_service import EmbeddingService
from app.embeddings.base_embedder import EmbeddingError
from app.vector_store.base_vector_store import BaseVectorStore
from app.vector_store.search_result import SearchResult
from app.vector_store.exceptions import VectorStoreError

from .retrieved_context import RetrievedContext
from .config import DEFAULT_TOP_K, MAX_CONTEXT_CHUNKS, MIN_SIMILARITY_SCORE
from .exceptions import (
    RetrieverError,
    RetrieverValidationError,
    RetrieverSearchError,
)

logger = logging.getLogger(__name__)


class Retriever:
    """Orchestrates semantic document retrieval for user queries.

    Receives EmbeddingService and BaseVectorStore via dependency injection.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: BaseVectorStore,
    ) -> None:
        """Initialize Retriever with injected dependencies.

        Args:
            embedding_service: Instance of EmbeddingService used to generate query vectors.
            vector_store: Instance of BaseVectorStore used to search nearest neighbors.

        Raises:
            RetrieverValidationError: If embedding_service or vector_store is None.
        """
        if embedding_service is None:
            raise RetrieverValidationError("embedding_service cannot be None")
        if vector_store is None:
            raise RetrieverValidationError("vector_store cannot be None")

        self.embedding_service = embedding_service
        self.vector_store = vector_store
        logger.info(
            "Initialized Retriever with %s and %s",
            type(embedding_service).__name__,
            type(vector_store).__name__,
        )

    def retrieve_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> RetrievedContext:
        """Retrieve relevant context for a user query.

        Args:
            query: The user search query string.
            top_k: Optional maximum number of results to retrieve. Defaults to config DEFAULT_TOP_K.
            min_score: Optional minimum similarity score threshold. Defaults to config MIN_SIMILARITY_SCORE.

        Returns:
            RetrievedContext object containing query metadata, matched SearchResult list, and latency.

        Raises:
            RetrieverValidationError: If query is empty or non-string.
            RetrieverSearchError: If embedding generation or vector store search fails.
        """
        if query is None or not isinstance(query, str) or not query.strip():
            logger.warning("Empty or invalid query string received by Retriever")
            raise RetrieverValidationError("query must be a non-empty string")

        clean_query = query.strip()
        effective_top_k = top_k if top_k is not None and top_k > 0 else DEFAULT_TOP_K
        effective_min_score = min_score if min_score is not None else MIN_SIMILARITY_SCORE

        logger.info("Processing query: '%s' (top_k=%d, min_score=%.2f)", clean_query, effective_top_k, effective_min_score)
        start_time = time.perf_counter()

        # Step 1: Generate query embedding using public EmbeddingService API
        try:
            query_vector = self.embedding_service.embed_query(clean_query)
            logger.debug("Generated query embedding with dimension %d", len(query_vector))
        except (EmbeddingError, Exception) as exc:
            logger.exception("Failed to generate query embedding: %s", exc)
            raise RetrieverSearchError(f"Failed to generate query embedding: {exc}") from exc

        # Step 2: Perform semantic search on VectorStore
        try:
            raw_results: List[SearchResult] = self.vector_store.search(
                query_embedding=query_vector,
                top_k=effective_top_k,
            )
            logger.debug("Vector store returned %d raw results", len(raw_results))
        except (VectorStoreError, Exception) as exc:
            logger.exception("Vector store search failed: %s", exc)
            raise RetrieverSearchError(f"Vector store search failed: {exc}") from exc

        # Step 3: Filter results by similarity score threshold
        filtered_results: List[SearchResult] = [
            r for r in raw_results if r.score >= effective_min_score
        ]

        # Step 4: Cap by MAX_CONTEXT_CHUNKS if exceeded
        if len(filtered_results) > MAX_CONTEXT_CHUNKS:
            logger.debug("Capping retrieved results from %d to MAX_CONTEXT_CHUNKS (%d)", len(filtered_results), MAX_CONTEXT_CHUNKS)
            filtered_results = filtered_results[:MAX_CONTEXT_CHUNKS]

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if not filtered_results:
            logger.warning("No vector search results satisfied min_score threshold %.2f", effective_min_score)
        else:
            logger.debug(
                "Retrieved %d matches. Scores: %s",
                len(filtered_results),
                [round(r.score, 4) for r in filtered_results],
            )

        logger.info("Retrieval completed in %.2f ms, returning %d results", latency_ms, len(filtered_results))

        return RetrievedContext(
            query=clean_query,
            results=filtered_results,
            retrieval_time_ms=latency_ms,
            top_k=effective_top_k,
        )
