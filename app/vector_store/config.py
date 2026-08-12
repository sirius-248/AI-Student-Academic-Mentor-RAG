"""Configuration defaults for the vector store module.

Centralizes vector store providers, file paths, and default search parameters.
Values can be overridden via environment variables.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Final

VECTOR_STORE_PROVIDER: Final[str] = os.getenv("VECTOR_STORE_PROVIDER", "faiss")
VECTOR_STORE_DIR: Final[Path] = Path(os.getenv("VECTOR_STORE_DIR", "data/vector_store"))
INDEX_FILENAME: Final[str] = os.getenv("VECTOR_STORE_INDEX_FILE", "index.faiss")
METADATA_FILENAME: Final[str] = os.getenv("VECTOR_STORE_METADATA_FILE", "metadata.pkl")
DEFAULT_TOP_K: Final[int] = int(os.getenv("VECTOR_STORE_DEFAULT_TOP_K", "5"))
