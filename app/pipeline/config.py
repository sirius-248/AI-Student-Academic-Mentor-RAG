"""Configuration for the application-level RAG orchestration package."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Small, infrastructure-neutral set of pipeline runtime options."""

    auto_save_index: bool = False
    default_top_k: int | None = None

    def __post_init__(self) -> None:
        if self.default_top_k is not None and self.default_top_k < 1:
            raise ValueError("default_top_k must be positive when supplied")

    @classmethod
    def from_environment(cls) -> "PipelineConfig":
        """Create configuration from optional pipeline-specific environment values."""
        raw_top_k = os.getenv("PIPELINE_DEFAULT_TOP_K", "").strip()
        return cls(
            auto_save_index=_as_bool(os.getenv("PIPELINE_AUTO_SAVE_INDEX", "false")),
            default_top_k=int(raw_top_k) if raw_top_k else None,
        )
