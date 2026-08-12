"""Citation model for the context used to generate an answer."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceReference:
    """A retrieved chunk's document provenance and relevance score."""

    document_id: str
    filename: str
    page_number: int | None
    similarity_score: float
    chunk_id: int | str | None = None
