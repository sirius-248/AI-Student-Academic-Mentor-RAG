"""Dependency construction and replaceable application-data services."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from fastapi import Request

from app.pipeline import RAGPipeline

from .config import APISettings


@dataclass(frozen=True, slots=True)
class RegisteredDocument:
    document_id: str
    filename: str
    local_path: Path
    indexed: bool = False
    course_id: str | None = None
    user_id: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class DocumentRegistry(Protocol):
    """Application-data boundary that can later be backed by PostgreSQL."""

    def get(self, document_id: str) -> RegisteredDocument | None: ...
    def register(self, document: RegisteredDocument) -> None: ...
    def mark_indexed(self, document_id: str) -> None: ...


class InMemoryDocumentRegistry:
    """Development-only registry; state is intentionally lost on restart."""

    def __init__(self) -> None:
        self._documents: dict[str, RegisteredDocument] = {}

    def get(self, document_id: str) -> RegisteredDocument | None:
        return self._documents.get(document_id)

    def register(self, document: RegisteredDocument) -> None:
        self._documents[document.document_id] = document

    def mark_indexed(self, document_id: str) -> None:
        document = self._documents[document_id]
        self._documents[document_id] = RegisteredDocument(
            document_id=document.document_id,
            filename=document.filename,
            local_path=document.local_path,
            indexed=True,
            course_id=document.course_id,
            user_id=document.user_id,
            metadata=document.metadata,
        )


def get_settings(request: Request) -> APISettings:
    return request.app.state.settings


def get_registry(request: Request) -> DocumentRegistry:
    return request.app.state.document_registry


def get_pipeline(request: Request) -> RAGPipeline:
    """Build the expensive RAG dependencies only when a RAG endpoint is used."""
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        pipeline = RAGPipeline()
        request.app.state.pipeline = pipeline
    return pipeline
