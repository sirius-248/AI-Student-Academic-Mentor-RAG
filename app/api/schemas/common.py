from __future__ import annotations

from pydantic import BaseModel, Field


class SourceResponse(BaseModel):
    document_id: str
    filename: str
    page_number: int | None = None
    similarity_score: float
    chunk_id: int | str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "ai-student-academic-mentor"


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
