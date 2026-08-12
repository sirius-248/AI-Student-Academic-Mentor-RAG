"""Response model returned by RAG question answering."""
from __future__ import annotations

from dataclasses import dataclass

from .source_reference import SourceReference


@dataclass(frozen=True, slots=True)
class AnswerResponse:
    """Immutable generated answer with provenance and execution metrics."""

    answer: str
    sources: tuple[SourceReference, ...]
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float
    prompt_context_length: int
    chunk_count: int
    model_name: str | None = None
