"""Document-upload HTTP adapter; indexing remains in RAGPipeline."""
from __future__ import annotations

import logging
import re
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ..config import APISettings
from ..dependencies import DocumentRegistry, RegisteredDocument, get_pipeline, get_registry, get_settings
from ..exceptions import APIError
from ..schemas import DocumentUploadResponse
from app.pipeline import RAGPipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])
_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")
_SAFE_DOCUMENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,254}$")


def _safe_filename(filename: str | None) -> str:
    candidate = _SAFE_FILENAME.sub("_", Path(filename or "document.pdf").name).strip("._")
    return candidate or "document.pdf"


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    document_id: str | None = Form(None),
    course_id: str | None = Form(None),
    user_id: str | None = Form(None),
    settings: APISettings = Depends(get_settings),
    registry: DocumentRegistry = Depends(get_registry),
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> DocumentUploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise APIError(400, "INVALID_FILE_TYPE", "Only PDF files may be uploaded.")
    supplied_id = document_id.strip() if document_id else ""
    if document_id is not None and not supplied_id:
        raise APIError(400, "INVALID_DOCUMENT_ID", "document_id must not be blank.")
    resolved_id = supplied_id or str(uuid.uuid4())
    if not _SAFE_DOCUMENT_ID.fullmatch(resolved_id):
        raise APIError(400, "INVALID_DOCUMENT_ID", "document_id may contain only letters, numbers, hyphens, and underscores.")
    if registry.get(resolved_id) is not None:
        raise APIError(409, "DOCUMENT_ALREADY_EXISTS", "A document with this document_id already exists.")

    filename = _safe_filename(file.filename)
    target_dir = settings.upload_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{resolved_id}_{filename}"
    started = time.perf_counter()
    size = 0
    first_chunk = True
    logger.info("Document upload received", extra={"document_id": resolved_id, "filename": filename})
    try:
        with target_path.open("xb") as destination:
            while content := await file.read(1024 * 1024):
                if first_chunk:
                    first_chunk = False
                    if not content[:1024].lstrip().startswith(b"%PDF-"):
                        raise APIError(400, "INVALID_PDF", "The uploaded file is not a valid PDF.")
                size += len(content)
                if size > settings.max_upload_size_bytes:
                    destination.close()
                    target_path.unlink(missing_ok=True)
                    raise APIError(413, "FILE_TOO_LARGE", f"The uploaded PDF exceeds the {settings.max_upload_size_mb} MB limit.")
                destination.write(content)
            if first_chunk:
                raise APIError(400, "INVALID_PDF", "The uploaded file is empty.")
    except APIError:
        target_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    registry.register(RegisteredDocument(resolved_id, filename, target_path, course_id=course_id, user_id=user_id))
    logger.info("Document uploaded", extra={"document_id": resolved_id, "filename": filename, "size_bytes": size})
    result = pipeline.index_document(target_path, document_id=resolved_id)
    registry.mark_indexed(resolved_id)
    logger.info("Document indexing completed", extra={"document_id": resolved_id, "request_latency_ms": round((time.perf_counter() - started) * 1000, 2)})
    return DocumentUploadResponse(
        document_id=result.document_id, filename=filename, indexing_status="indexed",
        pages_processed=result.pages_processed, chunks_created=result.chunks_created,
        vectors_added=result.vectors_added, processing_time_ms=result.processing_time_ms,
        course_id=course_id, user_id=user_id,
    )
