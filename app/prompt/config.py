"""Configuration defaults for the prompt builder module.

Centralizes maximum context lengths, default system prompts, and formatting settings.
Values can be overridden via environment variables.
"""
from __future__ import annotations

import os
from typing import Final

MAX_PROMPT_CONTEXT_LENGTH: Final[int] = int(os.getenv("MAX_PROMPT_CONTEXT_LENGTH", "16000"))
DEFAULT_SYSTEM_PROMPT: Final[str] = os.getenv(
    "DEFAULT_SYSTEM_PROMPT",
    "You are an expert AI Academic Mentor assisting students with educational materials.",
)
