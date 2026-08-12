"""Vector store module package.

Exposes vector store base abstractions, implementations, factory, search results, and exceptions.
"""
from .base_vector_store import BaseVectorStore
from .faiss_vector_store import FAISSVectorStore
from .vector_store_factory import VectorStoreFactory
from .search_result import SearchResult
from .exceptions import (
    VectorStoreError,
    VectorStoreInitializationError,
    VectorStoreValidationError,
    VectorStoreSearchError,
    VectorStorePersistenceError,
)

__all__ = [
    "BaseVectorStore",
    "FAISSVectorStore",
    "VectorStoreFactory",
    "SearchResult",
    "VectorStoreError",
    "VectorStoreInitializationError",
    "VectorStoreValidationError",
    "VectorStoreSearchError",
    "VectorStorePersistenceError",
]
