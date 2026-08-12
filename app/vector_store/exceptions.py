"""Vector store exceptions.

Defines a dedicated exception hierarchy for vector store operations.
"""
from __future__ import annotations


class VectorStoreError(Exception):
    """Base exception for all vector store errors."""


class VectorStoreInitializationError(VectorStoreError):
    """Raised when a vector store fails to initialize or load dependencies."""


class VectorStoreValidationError(VectorStoreError):
    """Raised when invalid inputs or mismatched vector dimensions are provided."""


class VectorStoreSearchError(VectorStoreError):
    """Raised when an error occurs during vector search."""


class VectorStorePersistenceError(VectorStoreError):
    """Raised when an error occurs during saving or loading vector store state from disk."""
