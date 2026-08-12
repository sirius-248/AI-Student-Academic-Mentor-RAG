"""Embedding providers package.

Expose embedding service, embedder factory, and common types for easy imports.
"""
from .base_embedder import (
    BaseEmbedder,
    EmbeddingError,
    EmbeddingInitializationError,
    EmbeddingValidationError,
    EmbeddingGenerationError,
    EmbedderError,
)
from .embedding_service import EmbeddingService
from .embedder_factory import EmbedderFactory
from .sentence_transformer_embedder import SentenceTransformerEmbedder
from .openai_embedder import OpenAIEmbedder
from .gemini_embedder import GeminiEmbedder
from .embed_utils import embed_document_chunks

__all__ = [
    "BaseEmbedder",
    "EmbeddingError",
    "EmbeddingInitializationError",
    "EmbeddingValidationError",
    "EmbeddingGenerationError",
    "EmbedderError",
    "EmbeddingService",
    "EmbedderFactory",
    "SentenceTransformerEmbedder",
    "OpenAIEmbedder",
    "GeminiEmbedder",
    "embed_document_chunks",
]

