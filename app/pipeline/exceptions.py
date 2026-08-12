"""Exception hierarchy for RAG pipeline orchestration."""
from __future__ import annotations


class PipelineError(Exception):
    """Base class for expected pipeline failures."""


class PipelineConfigurationError(PipelineError):
    """Raised when the pipeline has missing or incompatible dependencies."""


class PipelineValidationError(PipelineError):
    """Raised when a public pipeline operation receives invalid input."""


class PipelineIndexingError(PipelineError):
    """Raised when a document cannot be processed and indexed."""


class PipelineGenerationError(PipelineError):
    """Raised when retrieval, prompt building, or answer generation fails."""
