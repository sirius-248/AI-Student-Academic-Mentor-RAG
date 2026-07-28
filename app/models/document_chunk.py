"""Document chunk data model."""

from dataclasses import dataclass, field


@dataclass
class DocumentChunk:
    """Represents a chunk of text extracted from a document.

    Attributes:
        document_id: Unique identifier for the source document.
        chunk_id: Sequential identifier for this chunk within the document.
        text: The actual chunk content.
        source_file: Name or path of the source file.
        page_number: Page number where this chunk originated (optional).
        embedding: Vector embedding for semantic search (optional).
    """

    document_id: str
    chunk_id: int
    text: str
    source_file: str
    page_number: int | None = None
    embedding: list[float] | None = None
