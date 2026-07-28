"""Whitespace normalization cleaner."""

import logging
import re

from .base_cleaner import BaseCleaner

logger = logging.getLogger(__name__)


class WhitespaceCleaner(BaseCleaner):
    """Final normalization of whitespace.

    This is the last step in preprocessing. It:
    - Collapses multiple spaces
    - Collapses excessive blank lines
    - Trims trailing spaces on each line
    - Ensures consistent spacing
    """

    def __init__(self) -> None:
        """Initialize whitespace cleaner."""
        # Compile regex patterns once
        self._multiple_spaces = re.compile(r' {2,}')
        self._multiple_newlines = re.compile(r'\n{3,}')

    def clean(self, text: str) -> str:
        """Normalize all whitespace in text.

        Args:
            text: Input text.

        Returns:
            Text with normalized whitespace.
        """
        # Collapse multiple spaces to single space (but preserve intentional formatting)
        text = self._multiple_spaces.sub(' ', text)

        # Trim trailing spaces from each line
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        text = '\n'.join(lines)

        # Collapse multiple blank lines to at most 2 newlines (1 blank line)
        text = self._multiple_newlines.sub('\n\n', text)

        # Strip leading/trailing whitespace from entire document
        text = text.strip()

        logger.debug("Whitespace normalized")
        return text