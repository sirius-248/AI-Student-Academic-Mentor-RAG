"""Configuration for embedding defaults.

Centralizes default model and batch size selection so business logic doesn't
hardcode provider-specific defaults. Values can be overridden via environment
variables.
"""
from __future__ import annotations

import os
from typing import Final

DEFAULT_PROVIDER: Final[str] = os.getenv("EMBEDDING_PROVIDER", "sentence_transformer")
DEFAULT_MODEL: Final[str] = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
DEFAULT_BATCH_SIZE: Final[int] = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))
DEFAULT_DEVICE: Final[str] = os.getenv("EMBEDDING_DEVICE", "auto")

