"""Page number removal cleaner."""

import logging
import re

from .base_cleaner import BaseCleaner

logger = logging.getLogger(__name__)


class PageNumberCleaner(BaseCleaner):
    """Remove isolated page numbers from text.

    Removes lines that consist entirely of digits, which are typically
    page numbers. Does not remove numbers within normal text.
    """

    def __init__(self) -> None:
        """Initialize page number cleaner."""
        # Compile regex pattern once
        self._page_number_pattern = re.compile(r'^\d+$')

    def clean(self, text: str) -> str:
        """Remove isolated page numbers.

        Args:
            text: Input text.

        Returns:
            Text with isolated page numbers removed.
        """
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()
            # Only remove if the entire line is just a number
            if stripped and self._page_number_pattern.match(stripped):
                logger.debug(f"Removed page number: {stripped}")
                continue
            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)
