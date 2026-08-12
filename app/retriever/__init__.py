"""Retriever module package.

Exposes Retriever orchestration class, RetrievedContext model, and exceptions.
"""
from .retriever import Retriever
from .retrieved_context import RetrievedContext
from .exceptions import (
    RetrieverError,
    RetrieverValidationError,
    RetrieverSearchError,
)

__all__ = [
    "Retriever",
    "RetrievedContext",
    "RetrieverError",
    "RetrieverValidationError",
    "RetrieverSearchError",
]
