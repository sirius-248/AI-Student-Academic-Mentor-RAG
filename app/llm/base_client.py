"""Base LLM client abstractions for the AI Academic Mentor."""

from abc import ABC, abstractmethod


class LLMClientError(Exception):
    """Base exception type for LLM client failures."""


class BaseLLMClient(ABC):
    """Abstract base class for language model clients."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text for the provided prompt."""
        raise NotImplementedError
