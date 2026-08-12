from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from .common import SourceResponse


class QuestionRequest(BaseModel):
    document_id: str = Field(min_length=1, max_length=255)
    question: str = Field(min_length=1, max_length=4_000)

    @field_validator("document_id", "question")
    @classmethod
    def must_not_be_whitespace(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class QuestionResponse(BaseModel):
    document_id: str
    question: str
    answer: str
    sources: list[SourceResponse]
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float
    model_name: str | None = None
    prompt_context_length: int
    chunk_count: int
