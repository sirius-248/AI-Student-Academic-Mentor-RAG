"""Dependency construction and replaceable application-data services."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from fastapi import Request

from app.pipeline import RAGPipeline
from app.vector_store import config as vector_config
from app.vector_store.vector_store_factory import VectorStoreFactory

from .config import APISettings

logger = logging.getLogger(__name__)


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


def recover_document_registry_from_vector_store(
    registry: InMemoryDocumentRegistry,
    vector_store,
    settings: APISettings,
) -> None:
    """Rebuild an in-memory registry from the persisted FAISS metadata map.

    The protocol stays the same for the API dependency boundary, so a PostgreSQL
    implementation can later replace only the registry object without touching routes.
    """
    metadata_map = getattr(vector_store, "_metadata_map", None)
    if not metadata_map:
        logger.info("No persisted FAISS metadata entries were found for registry reconstruction.")
        return

    seen: set[str] = set()
    for chunk in metadata_map.values():
        document_id = getattr(chunk, "document_id", None)
        if not document_id or document_id in seen:
            continue
        seen.add(document_id)
        filename = getattr(chunk, "source_file", "document.pdf")
        local_path = settings.upload_dir / f"{document_id}_{filename}"
        registry.register(RegisteredDocument(document_id, filename, local_path, indexed=True))

    logger.info("Reconstructed document registry from %d persisted FAISS document chunks.", len(seen))


def load_vector_store_from_persistence(vector_store, settings: APISettings | None = None) -> object:
    """Load the persisted FAISS vector store if the index and metadata files exist.

    Missing or corrupt persisted state is handled without interrupting startup.
    """
    index_path = Path(vector_config.VECTOR_STORE_DIR) / vector_config.INDEX_FILENAME
    metadata_path = Path(vector_config.VECTOR_STORE_DIR) / vector_config.METADATA_FILENAME
    if not index_path.exists() and not metadata_path.exists():
        logger.info("No persisted FAISS vector store found at %s; starting fresh.", vector_config.VECTOR_STORE_DIR)
        return vector_store

    if not index_path.exists() or not metadata_path.exists():
        logger.warning(
            "Partial persisted FAISS vector store found at %s; missing %s%s. "
            "Starting with an empty in-memory vector store and registry.",
            vector_config.VECTOR_STORE_DIR,
            "index.faiss" if not index_path.exists() else "",
            "metadata.pkl" if not metadata_path.exists() else "",
        )
        return vector_store

    try:
        vector_store.load(directory=vector_config.VECTOR_STORE_DIR)
    except Exception as exc:
        logger.exception(
            "Persisted FAISS vector store was found at %s but could not be loaded; "
            "starting with an empty in-memory vector store and registry. "
            "The persisted files may be corrupt or incomplete: %s",
            vector_config.VECTOR_STORE_DIR,
            exc,
        )
        return VectorStoreFactory.get_vector_store()

    logger.info("Loaded persisted FAISS vector store from %s", vector_config.VECTOR_STORE_DIR)
    return vector_store


def get_pipeline(request: Request) -> RAGPipeline:
    """Build the expensive RAG dependencies only when a RAG endpoint is used."""
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        pipeline = RAGPipeline(vector_store=request.app.state.vector_store)
        request.app.state.pipeline = pipeline
    return pipeline
