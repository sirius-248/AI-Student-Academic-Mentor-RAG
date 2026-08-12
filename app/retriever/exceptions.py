"""Retriever exception hierarchy.

Defines dedicated exceptions for retrieval validation and execution failures.
"""
from __future__ import annotations


class RetrieverError(Exception):
    """Base exception for all retriever-related errors."""


class RetrieverValidationError(RetrieverError):
    """Raised when invalid inputs (e.g., empty query, invalid parameters) are provided."""


class RetrieverSearchError(RetrieverError):
    """Raised when an error occurs during query embedding or vector store search."""
