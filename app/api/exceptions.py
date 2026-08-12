"""Structured API errors and mappings from pipeline errors."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.pipeline import (
    PipelineConfigurationError,
    PipelineGenerationError,
    PipelineIndexingError,
    PipelineValidationError,
)

logger = logging.getLogger(__name__)


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def handle_api_error(_: Request, exc: APIError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(PipelineValidationError)
    async def handle_pipeline_validation(_: Request, exc: PipelineValidationError) -> JSONResponse:
        return error_response(400, "PIPELINE_VALIDATION_ERROR", str(exc))

    @app.exception_handler(PipelineIndexingError)
    async def handle_pipeline_indexing(_: Request, exc: PipelineIndexingError) -> JSONResponse:
        logger.error("RAG indexing failure", exc_info=exc)
        return error_response(500, "INDEXING_FAILED", "The document could not be indexed.")

    @app.exception_handler(PipelineGenerationError)
    async def handle_pipeline_generation(_: Request, exc: PipelineGenerationError) -> JSONResponse:
        logger.error("RAG generation failure", exc_info=exc)
        return error_response(503, "ANSWERING_UNAVAILABLE", "Answer generation is temporarily unavailable.")

    @app.exception_handler(PipelineConfigurationError)
    async def handle_pipeline_configuration(_: Request, exc: PipelineConfigurationError) -> JSONResponse:
        logger.error("RAG configuration failure", exc_info=exc)
        return error_response(503, "RAG_UNAVAILABLE", "The RAG service is not currently available.")

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, __: RequestValidationError) -> JSONResponse:
        return error_response(422, "VALIDATION_ERROR", "The request data is invalid.")

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API error", exc_info=exc)
        return error_response(500, "INTERNAL_SERVER_ERROR", "An unexpected server error occurred.")
