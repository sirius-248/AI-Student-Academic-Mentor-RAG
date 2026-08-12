"""Document metadata owned by the pipeline boundary."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    """Stable metadata describing a source document without its text content."""

    document_id: str
    filename: str
    source_path: str
    page_count: int | None = None

    @classmethod
    def from_path(cls, path: str | Path, document_id: str | None = None, page_count: int | None = None) -> "DocumentMetadata":
        """Build metadata using a file path and an optional caller-provided ID."""
        source = Path(path)
        return cls(
            document_id=document_id or source.stem,
            filename=source.name,
            source_path=str(source),
            page_count=page_count,
        )
