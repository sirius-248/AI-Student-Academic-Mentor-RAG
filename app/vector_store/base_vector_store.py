"""Base vector store abstraction.

Defines the abstract interface that every vector database integration must implement.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence, List, Union, Optional

from app.models.document_chunk import DocumentChunk
from .search_result import SearchResult


class BaseVectorStore(ABC):
    """Abstract base class for vector store implementations."""

    @abstractmethod
    def add_documents(self, chunks: Sequence[DocumentChunk]) -> None:
        """Add a collection of DocumentChunk objects with embeddings to the vector store.

        Args:
            chunks: Sequence of DocumentChunk instances. Each chunk must contain a valid embedding vector.
        """
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query_embedding: Sequence[float],
        top_k: int = 5,
        document_ids: Sequence[str] | None = None,
    ) -> List[SearchResult]:
        """Perform a nearest-neighbor vector similarity search.

        Args:
            query_embedding: Float vector representing the query embedding.
            top_k: Number of nearest neighbors to retrieve.
            document_ids: Optional set of document IDs to scope the candidate
                search space before selecting top_k.

        Returns:
            List of SearchResult objects sorted by descending similarity score.
        """
        raise NotImplementedError

    @abstractmethod
    def save(self, directory: Optional[Union[str, Path]] = None) -> None:
        """Persist the vector store index and metadata to disk.

        Args:
            directory: Optional target directory path. If None, uses configured default directory.
        """
        raise NotImplementedError

    @abstractmethod
    def load(self, directory: Optional[Union[str, Path]] = None) -> None:
        """Restore the vector store index and metadata from disk.

        Args:
            directory: Optional target directory path. If None, uses configured default directory.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all stored vectors and metadata, resetting the index state."""
        raise NotImplementedError

    @abstractmethod
    def is_empty(self) -> bool:
        """Check if the vector store contains any vectors.

        Returns:
            True if the vector store is empty, False otherwise.
        """
        raise NotImplementedError
