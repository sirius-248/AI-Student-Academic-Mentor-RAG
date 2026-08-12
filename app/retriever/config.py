"""Configuration defaults for the retriever module.

Centralizes retrieval parameters such as DEFAULT_TOP_K, MAX_CONTEXT_CHUNKS,
and MIN_SIMILARITY_SCORE. Values can be overridden via environment variables.
"""
from __future__ import annotations

import os
from typing import Final

DEFAULT_TOP_K: Final[int] = int(os.getenv("RETRIEVAL_DEFAULT_TOP_K", "5"))
MAX_CONTEXT_CHUNKS: Final[int] = int(os.getenv("RETRIEVAL_MAX_CONTEXT_CHUNKS", "10"))
MIN_SIMILARITY_SCORE: Final[float] = float(os.getenv("RETRIEVAL_MIN_SIMILARITY_SCORE", "0.0"))
