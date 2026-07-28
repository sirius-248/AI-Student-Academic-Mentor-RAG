"""Base class for all text cleaners."""

from abc import ABC, abstractmethod


class BaseCleaner(ABC):
    """Abstract base class for preprocessing cleaners."""

    @abstractmethod
    def clean(self, text: str) -> str:
        """Clean and transform text.

        Args:
            text: Raw text to clean.

        Returns:
            Cleaned text.
        """
        raise NotImplementedError