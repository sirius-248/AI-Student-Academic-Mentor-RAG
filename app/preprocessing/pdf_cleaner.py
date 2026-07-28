"""PDF text normalization cleaner."""

import logging
import re
import unicodedata

from .base_cleaner import BaseCleaner

logger = logging.getLogger(__name__)


class PDFCleaner(BaseCleaner):
    """Normalize raw text extracted from PDFs.

    Handles:
    - Non-breaking spaces
    - Soft hyphen characters
    - Unicode whitespace normalization
    - Tab to space conversion
    - Line ending normalization
    - Control character removal
    - Paragraph boundary preservation
    """

    def __init__(self) -> None:
        """Initialize PDF cleaner."""
        # Compile regex for control characters once
        self._control_char_pattern = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]')

    def clean(self, text: str) -> str:
        """Clean and normalize PDF-extracted text.

        Args:
            text: Raw PDF text.

        Returns:
            Normalized text with preserved paragraph structure.
        """
        # Replace non-breaking spaces with regular spaces
        text = text.replace('\u00A0', ' ')

        # Remove soft hyphens
        text = text.replace('\u00AD', '')

        # Normalize unicode whitespace
        text = ''.join(
            ' ' if unicodedata.category(char) in ('Zs', 'Zl', 'Zp') else char
            for char in text
        )

        # Replace tabs with spaces
        text = text.replace('\t', ' ')

        # Normalize line endings to \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove control characters
        text = self._control_char_pattern.sub('', text)

        logger.debug("PDF text normalized")
        return text