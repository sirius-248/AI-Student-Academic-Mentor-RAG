"""Question HTTP adapter; answer generation remains in RAGPipeline."""
from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends

from ..config import APISettings
from ..dependencies import DocumentRegistry, get_pipeline, get_registry, get_settings
from ..exceptions import APIError
from ..schemas import QuestionRequest, QuestionResponse, SourceResponse
from app.pipeline import RAGPipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    payload: QuestionRequest,
    registry: DocumentRegistry = Depends(get_registry),
    settings: APISettings = Depends(get_settings),
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> QuestionResponse:
    if len(payload.question) > settings.max_question_length:
        raise APIError(422, "QUESTION_TOO_LONG", f"question must be at most {settings.max_question_length} characters.")
    document = registry.get(payload.document_id)
    if document is None or not document.indexed:
        raise APIError(404, "DOCUMENT_NOT_FOUND", "The requested document has not been indexed.")
    started = time.perf_counter()
    logger.info("Question received", extra={"document_id": payload.document_id, "question_length": len(payload.question)})
    result = pipeline.answer_question(payload.question, document_ids=[payload.document_id])
    logger.info("Question answered", extra={"document_id": payload.document_id, "request_latency_ms": round((time.perf_counter() - started) * 1000, 2)})
    return QuestionResponse(
        document_id=payload.document_id, question=payload.question, answer=result.answer,
        sources=[
            SourceResponse(
                document_id=source.document_id,
                filename=source.filename,
                page_number=source.page_number,
                similarity_score=source.similarity_score,
                chunk_id=source.chunk_id,
            )
            for source in result.sources
        ],
        retrieval_time_ms=result.retrieval_time_ms, generation_time_ms=result.generation_time_ms,
        total_time_ms=result.total_time_ms, model_name=result.model_name,
        prompt_context_length=result.prompt_context_length, chunk_count=result.chunk_count,
    )
