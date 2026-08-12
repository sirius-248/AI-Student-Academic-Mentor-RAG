"""Result model returned after a document has been indexed."""
from __future__ import annotations

from dataclasses import dataclass

from .document_metadata import DocumentMetadata


@dataclass(frozen=True, slots=True)
class IndexingResult:
    """Immutable summary of one successful indexing operation."""

    document: DocumentMetadata
    chunks_created: int
    vectors_added: int
    processing_time_ms: float

    @property
    def document_id(self) -> str:
        """Compatibility-friendly access to the indexed document identifier."""
        return self.document.document_id

    @property
    def document_name(self) -> str:
        """Compatibility-friendly access to the source filename."""
        return self.document.filename

    @property
    def pages_processed(self) -> int | None:
        """Number of source pages when the reader supplied it."""
        return self.document.page_count

    @property
    def success(self) -> bool:
        """Indexing results are only created after successful completion."""
        return True
