"""Watermark and unwanted text pattern removal."""

import logging
import re

from .base_cleaner import BaseCleaner

logger = logging.getLogger(__name__)


class WatermarkCleaner(BaseCleaner):
    """Remove watermark patterns from text.

    Uses configurable regex patterns to detect and remove common watermarks
    such as websites, domain names, and repeated promotional text.
    """

    DEFAULT_PATTERNS = [
        r"\bwww\.[^\s]+\b",
        r"\b[a-zA-Z0-9-]+\.(com|net|org|edu|in|co\.uk)\b",
        r"https?://[^\s]+",
    ]

    def __init__(self, patterns: list[str] | None = None) -> None:
        """Initialize watermark cleaner with regex patterns.

        Args:
            patterns: Optional list of regex patterns to match watermarks.
                     Uses DEFAULT_PATTERNS if not provided.
        """
        self.patterns = patterns or self.DEFAULT_PATTERNS
        # Compile regexes once for efficiency
        self._compiled_patterns = [re.compile(pattern) for pattern in self.patterns]
        logger.debug(f"Watermark cleaner initialized with {len(self._compiled_patterns)} patterns")

    def clean(self, text: str) -> str:
        """Remove watermark patterns from text.

        Removes entire lines that match watermark patterns without affecting
        normal content within paragraphs.

        Args:
            text: Input text.

        Returns:
            Text with watermark lines removed.
        """
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Check if the entire line matches a watermark pattern
            if self._is_watermark_line(line):
                logger.debug(f"Removed watermark line: {line[:50]}...")
                continue
            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _is_watermark_line(self, line: str) -> bool:
        """Check if a line is primarily a watermark.

        Args:
            line: Line of text to check.

        Returns:
            True if line matches a watermark pattern.
        """
        stripped = line.strip()
        if not stripped:
            return False

        # Check each pattern
        for pattern in self._compiled_patterns:
            # If the pattern matches and covers most of the line, it's a watermark
            match = pattern.search(stripped)
            if match:
                match_length = len(match.group())
                # If match is more than 50% of the line, consider it a watermark
                if match_length > len(stripped) * 0.5:
                    return True

        return False