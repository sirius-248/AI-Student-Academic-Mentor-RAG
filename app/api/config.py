"""Configuration owned by the HTTP API layer."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True, slots=True)
class APISettings:
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: tuple[str, ...] = ("http://localhost:3000", "http://localhost:5173")
    upload_dir: Path = Path("data/uploads")
    max_upload_size_mb: int = 20
    max_question_length: int = 4_000

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @classmethod
    def from_environment(cls) -> "APISettings":
        origins = _csv(os.getenv("API_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"))
        max_size = int(os.getenv("API_MAX_UPLOAD_SIZE_MB", "20"))
        max_question = int(os.getenv("API_MAX_QUESTION_LENGTH", "4000"))
        if max_size < 1 or max_question < 1:
            raise ValueError("API size limits must be positive")
        return cls(
            host=os.getenv("API_HOST", "127.0.0.1"),
            port=int(os.getenv("API_PORT", "8000")),
            cors_origins=origins,
            upload_dir=Path(os.getenv("API_UPLOAD_DIR", "data/uploads")),
            max_upload_size_mb=max_size,
            max_question_length=max_question,
        )
