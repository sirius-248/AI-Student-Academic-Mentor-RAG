from __future__ import annotations

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    indexing_status: str
    pages_processed: int | None = None
    chunks_created: int
    vectors_added: int
    processing_time_ms: float
    course_id: str | None = None
    user_id: str | None = None
