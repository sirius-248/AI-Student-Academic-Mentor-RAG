"""Prompt builder exceptions.

Defines a dedicated exception hierarchy for prompt validation and building failures.
"""
from __future__ import annotations


class PromptBuilderError(Exception):
    """Base exception for all prompt builder errors."""


class PromptValidationError(PromptBuilderError):
    """Raised when invalid inputs (e.g., empty question, missing request) are provided."""
