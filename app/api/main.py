"""FastAPI application composition; no RAG business logic belongs here."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import APISettings
from .dependencies import InMemoryDocumentRegistry
from .exceptions import register_exception_handlers
from .routes import documents, health, questions


def create_app(settings: APISettings | None = None) -> FastAPI:
    settings = settings or APISettings.from_environment()
    app = FastAPI(title="AI Student Academic Mentor API", version="1.0.0")
    app.state.settings = settings
    app.state.document_registry = InMemoryDocumentRegistry()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(questions.router, prefix="/api/v1")
    register_exception_handlers(app)
    return app


app = create_app()
