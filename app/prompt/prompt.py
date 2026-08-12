"""Data model for constructed LLM prompts.

Encapsulates the system prompt, user prompt, full prompt, and context metrics.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Prompt:
    """Represents a fully constructed prompt object.

    Attributes:
        system_prompt: The system instruction prompt string.
        user_prompt: The formatted user query and context block string.
        full_prompt: The complete composed prompt string ready for LLM generation.
        context_length: Character length of the formatted context block.
        chunk_count: Number of DocumentChunk objects formatted into context.
    """

    system_prompt: str
    user_prompt: str
    full_prompt: str
    context_length: int
    chunk_count: int
