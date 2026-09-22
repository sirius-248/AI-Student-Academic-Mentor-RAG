"""FAISS vector store implementation.

Provides cosine similarity vector search and persistence using FAISS IndexFlatIP
and L2 vector normalization.
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Sequence, List, Dict, Optional, Union, Any

import numpy as np

from app.models.document_chunk import DocumentChunk
from .base_vector_store import BaseVectorStore
from .search_result import SearchResult
from .config import (
    VECTOR_STORE_DIR,
    INDEX_FILENAME,
    METADATA_FILENAME,
    DEFAULT_TOP_K,
)
from .exceptions import (
    VectorStoreInitializationError,
    VectorStoreValidationError,
    VectorStoreSearchError,
    VectorStorePersistenceError,
)

logger = logging.getLogger(__name__)


class FAISSVectorStore(BaseVectorStore):
    """Production-ready vector store using FAISS for cosine similarity search.

    Uses faiss.IndexFlatIP combined with L2 vector normalization to calculate
    exact cosine similarity.
    """

    def __init__(self, embedding_dim: Optional[int] = None) -> None:
        """Initialize FAISSVectorStore.

        Args:
            embedding_dim: Optional dimension of vector embeddings. If provided,
                          initializes the FAISS index immediately.
        """
        self._index: Optional[Any] = None
        self._metadata_map: Dict[int, DocumentChunk] = {}
        self._vector_count: int = 0
        self._embedding_dim: Optional[int] = embedding_dim

        if embedding_dim is not None:
            self._init_index(embedding_dim)

    def _init_index(self, dimension: int) -> None:
        """Initialize a new FAISS IndexFlatIP index for the given dimension."""
        try:
            import faiss

            self._index = faiss.IndexFlatIP(dimension)
            self._embedding_dim = dimension
            logger.info("Initialized new FAISS IndexFlatIP with dimension %d", dimension)
        except Exception as exc:
            logger.exception("Failed to initialize FAISS index: %s", exc)
            raise VectorStoreInitializationError(f"Failed to initialize FAISS index: {exc}") from exc

    def is_empty(self) -> bool:
        """Return True if the vector store contains no vectors, False otherwise."""
        return self._vector_count == 0 or self._index is None

    def add_documents(self, chunks: Sequence[DocumentChunk]) -> None:
        """Add a collection of pre-embedded DocumentChunk objects to the FAISS index.

        Args:
            chunks: Sequence of DocumentChunk objects with populated .embedding vectors.

        Raises:
            VectorStoreValidationError: If input is invalid, embeddings are missing,
                                      or vector dimensions mismatch.
        """
        if chunks is None:
            raise VectorStoreValidationError("chunks must be a sequence of DocumentChunk instances (got None)")

        try:
            chunk_list = list(chunks)
        except TypeError as exc:
            raise VectorStoreValidationError("chunks must be an iterable sequence of DocumentChunk instances") from exc

        if not chunk_list:
            logger.warning("add_documents called with an empty collection of chunks")
            return

        # Validate that all chunks have non-empty embeddings and consistent dimensionality
        vectors: List[List[float]] = []
        for i, chunk in enumerate(chunk_list):
            if chunk is None:
                raise VectorStoreValidationError(f"Chunk at index {i} is None")
            if chunk.embedding is None or len(chunk.embedding) == 0:
                logger.warning("Chunk %s at index %d has no embedding vector", getattr(chunk, "chunk_id", i), i)
                raise VectorStoreValidationError(f"Chunk at index {i} is missing embedding vector")
            vectors.append(chunk.embedding)

        detected_dim = len(vectors[0])

        # Validate dimensional consistency across input chunks
        for i, vec in enumerate(vectors):
            if len(vec) != detected_dim:
                logger.warning("Dimension mismatch at index %d: expected %d, got %d", i, detected_dim, len(vec))
                raise VectorStoreValidationError(
                    f"Dimension mismatch at index {i}: expected {detected_dim}, got {len(vec)}"
                )

        # Initialize index if not already created
        if self._index is None:
            self._init_index(detected_dim)
        elif detected_dim != self._embedding_dim:
            logger.warning("Chunk dimension %d does not match index dimension %d", detected_dim, self._embedding_dim)
            raise VectorStoreValidationError(
                f"Chunk vector dimension {detected_dim} does not match vector store dimension {self._embedding_dim}"
            )

        # Convert to numpy float32 matrix and normalize L2 for cosine similarity
        import faiss

        vectors_np = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(vectors_np)

        start_id = self._vector_count
        try:
            self._index.add(vectors_np)
        except Exception as exc:
            logger.exception("Failed to add vectors to FAISS index: %s", exc)
            raise VectorStoreError(f"FAISS add failed: {exc}") from exc

        # Update metadata mapping
        for idx, chunk in enumerate(chunk_list):
            faiss_id = start_id + idx
            self._metadata_map[faiss_id] = chunk

        self._vector_count += len(chunk_list)
        logger.debug("Added %d vectors (dim=%d) to FAISS index. Total vector count: %d", len(chunk_list), detected_dim, self._vector_count)
        logger.info("Successfully added %d DocumentChunk objects to vector store", len(chunk_list))

    def search(
        self,
        query_embedding: Sequence[float],
        top_k: int = DEFAULT_TOP_K,
        document_ids: Sequence[str] | None = None,
    ) -> List[SearchResult]:
        """Search for the top_k nearest neighbors using cosine similarity.

        Args:
            query_embedding: Float vector representing the query embedding.
            top_k: Maximum number of nearest results to return.
            document_ids: Optional set of document IDs to scope the candidate
                search space before top_k selection.

        Returns:
            List of SearchResult objects sorted by descending similarity score.

        Raises:
            VectorStoreValidationError: If query_embedding is invalid or dimension mismatches.
            VectorStoreSearchError: If FAISS search fails.
        """
        if query_embedding is None:
            raise VectorStoreValidationError("query_embedding cannot be None")

        query_vec = list(query_embedding)
        if not query_vec:
            raise VectorStoreValidationError("query_embedding cannot be empty")

        if self.is_empty():
            logger.warning("Search called on an empty vector store")
            return []

        if len(query_vec) != self._embedding_dim:
            logger.warning("Query vector dimension %d does not match index dimension %d", len(query_vec), self._embedding_dim)
            raise VectorStoreValidationError(
                f"Query vector dimension {len(query_vec)} does not match vector store dimension {self._embedding_dim}"
            )

        import faiss
        top_k = max(1, int(top_k))

        # Preserve the current behavior when no document scope is supplied.
        if document_ids is None:
            effective_k = min(top_k, self._vector_count)
            query_np = np.array([query_vec], dtype=np.float32)
            faiss.normalize_L2(query_np)
            try:
                distances, indices = self._index.search(query_np, k=effective_k)
            except Exception as exc:
                logger.exception("FAISS search execution failed: %s", exc)
                raise VectorStoreSearchError(f"FAISS search failed: {exc}") from exc

            results: List[SearchResult] = []
            if len(indices) > 0:
                for idx, score in zip(indices[0], distances[0]):
                    if idx == -1:
                        continue
                    chunk = self._metadata_map.get(int(idx))
                    if chunk is not None:
                        results.append(SearchResult(chunk=chunk, score=float(score)))
                    else:
                        logger.warning("FAISS index returned ID %d not found in metadata map", idx)

            logger.debug("Search returned %d results for top_k=%d", len(results), top_k)
            logger.info("Search completed successfully, returned %d matches", len(results))
            return results

        # Document-aware branch: scope the metadata map to requested docs only
        # and rank only those stored vectors in a temporary in-memory FAISS
        # index, without mutating persisted index or metadata representation.
        requested_ids = frozenset(str(item).strip() for item in document_ids if isinstance(item, str) and str(item).strip())
        if not requested_ids:
            raise VectorStoreValidationError("document_ids must contain at least one non-empty ID")

        eligible_ids = []
        eligible_vectors = []
        for faiss_id, chunk in self._metadata_map.items():
            if chunk is None:
                continue
            if getattr(chunk, "document_id", None) not in requested_ids:
                continue
            if chunk.embedding is None:
                continue
            eligible_ids.append(faiss_id)
            eligible_vectors.append(np.array(chunk.embedding, dtype=np.float32))

        if not eligible_ids:
            logger.warning("No eligible document-aware vectors found for document_ids=%s", sorted(requested_ids))
            return []

        vector_matrix = np.array(eligible_vectors, dtype=np.float32)
        faiss.normalize_L2(vector_matrix)

        query_np = np.array([query_vec], dtype=np.float32)
        faiss.normalize_L2(query_np)

        local_index = faiss.IndexFlatIP(self._embedding_dim)
        local_index.add(vector_matrix)

        effective_k = min(top_k, len(eligible_ids))
        try:
            distances, indices = local_index.search(query_np, k=effective_k)
        except Exception as exc:
            logger.exception("FAISS document-aware search execution failed: %s", exc)
            raise VectorStoreSearchError(f"FAISS document-aware search failed: {exc}") from exc

        results: List[SearchResult] = []
        if len(indices) > 0:
            for local_idx, score in zip(indices[0], distances[0]):
                if local_idx == -1:
                    continue
                original_faiss_id = eligible_ids[int(local_idx)]
                chunk = self._metadata_map.get(original_faiss_id)
                if chunk is not None:
                    results.append(SearchResult(chunk=chunk, score=float(score)))
                else:
                    logger.warning("Metadata map missed eligible FAISS id %d", original_faiss_id)

        logger.debug("Document-aware search returned %d results for top_k=%d on document_ids=%s", len(results), top_k, sorted(requested_ids))
        logger.info("Search completed successfully, returned %d document-aware matches", len(results))
        return results

    def _save_metadata(self, filepath: Path) -> None:
        """Encapsulated private helper to save metadata dictionary and state attributes to disk."""
        state = {
            "metadata_map": self._metadata_map,
            "vector_count": self._vector_count,
            "embedding_dim": self._embedding_dim,
        }
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "wb") as f:
                pickle.dump(state, f)
            logger.debug("Saved metadata map with %d entries to %s", len(self._metadata_map), filepath)
        except Exception as exc:
            logger.exception("Failed to write metadata file %s: %s", filepath, exc)
            raise VectorStorePersistenceError(f"Failed to write metadata file {filepath}: {exc}") from exc

    def _load_metadata(self, filepath: Path) -> Dict[str, Any]:
        """Encapsulated private helper to load metadata dictionary and state attributes from disk."""
        try:
            with open(filepath, "rb") as f:
                state = pickle.load(f)
            logger.debug("Loaded metadata file from %s", filepath)
            return state
        except Exception as exc:
            logger.exception("Failed to read metadata file %s: %s", filepath, exc)
            raise VectorStorePersistenceError(f"Failed to read metadata file {filepath}: {exc}") from exc

    def save(self, directory: Optional[Union[str, Path]] = None) -> None:
        """Save FAISS index and metadata map to disk.

        Args:
            directory: Directory path where index and metadata will be saved.
                       Defaults to VECTOR_STORE_DIR from config.
        """
        if self.is_empty():
            logger.warning("Attempted to save an empty vector store")

        target_dir = Path(directory) if directory else VECTOR_STORE_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        index_path = target_dir / INDEX_FILENAME
        metadata_path = target_dir / METADATA_FILENAME

        import faiss

        try:
            if self._index is not None:
                faiss.write_index(self._index, str(index_path))
                logger.info("Saved FAISS index to %s", index_path)
            self._save_metadata(metadata_path)
            logger.info("Successfully persisted vector store state to %s", target_dir)
        except Exception as exc:
            logger.exception("Failed to persist vector store: %s", exc)
            raise VectorStorePersistenceError(f"Failed to persist vector store to {target_dir}: {exc}") from exc

    def load(self, directory: Optional[Union[str, Path]] = None) -> None:
        """Load FAISS index and metadata map from disk.

        Args:
            directory: Directory path containing saved index and metadata files.
                       Defaults to VECTOR_STORE_DIR from config.
        """
        target_dir = Path(directory) if directory else VECTOR_STORE_DIR
        index_path = target_dir / INDEX_FILENAME
        metadata_path = target_dir / METADATA_FILENAME

        if not index_path.exists():
            raise VectorStorePersistenceError(f"Index file not found at {index_path}")
        if not metadata_path.exists():
            raise VectorStorePersistenceError(f"Metadata file not found at {metadata_path}")

        import faiss

        try:
            self._index = faiss.read_index(str(index_path))
            logger.info("Loaded FAISS index from %s", index_path)
            state = self._load_metadata(metadata_path)

            self._metadata_map = state.get("metadata_map", {})
            self._vector_count = state.get("vector_count", len(self._metadata_map))
            self._embedding_dim = state.get("embedding_dim", self._index.d)

            logger.info(
                "Successfully restored vector store state from %s (%d vectors, dim=%d)",
                target_dir,
                self._vector_count,
                self._embedding_dim,
            )
        except Exception as exc:
            logger.exception("Failed to load vector store from %s: %s", target_dir, exc)
            raise VectorStorePersistenceError(f"Failed to load vector store from {target_dir}: {exc}") from exc

    def clear(self) -> None:
        """Clear all stored vectors and metadata, resetting state."""
        self._index = None
        self._metadata_map.clear()
        self._vector_count = 0
        self._embedding_dim = None
        logger.info("Cleared vector store state and metadata")
