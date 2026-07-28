"""Header and footer detection and removal."""

import logging
import re
from collections import Counter

from .base_cleaner import BaseCleaner

logger = logging.getLogger(__name__)


class HeaderFooterCleaner(BaseCleaner):
    """Automatically detect and remove repeated headers and footers.

    Uses frequency analysis with advanced heuristics to identify lines that
    appear multiple times and are likely headers/footers rather than content.

    Works generically across textbooks, research papers, lecture notes, etc.
    without hardcoded document-specific strings.
    """

    def __init__(
        self,
        min_frequency: int = 3,
        max_line_length: int = 80,
        max_line_words: int = 10,
    ) -> None:
        """Initialize header/footer cleaner.

        Args:
            min_frequency: Minimum times a line must appear to be considered header/footer.
            max_line_length: Maximum character length for header/footer candidates.
            max_line_words: Maximum word count for header/footer candidates.
        """
        self.min_frequency = min_frequency
        self.max_line_length = max_line_length
        self.max_line_words = max_line_words

        # Precompile patterns
        self._pure_number = re.compile(r'^\d+$')
        self._ends_with_period = re.compile(r'\.\s*$')
        self._special_char_ratio = re.compile(r'[^\w\s-]')

    def clean(self, text: str) -> str:
        """Remove repeated header and footer lines.

        Args:
            text: Input text.

        Returns:
            Text with detected headers/footers removed.
        """
        lines = text.split('\n')
        
        # Need at least a few lines to detect patterns (3 minimum for a repeated line)
        if len(lines) < 3:
            logger.debug("Too few lines for header/footer detection")
            return text

        # Find lines to remove
        lines_to_remove = self._find_headers_and_footers(lines)

        if not lines_to_remove:
            logger.info("HeaderFooterCleaner: No headers/footers detected")
            return text

        # Remove complete lines
        cleaned_lines = [
            line for line in lines
            if self._normalize_line(line.strip()) not in lines_to_remove
        ]

        # Log statistics
        removed_count = len(lines) - len(cleaned_lines)
        logger.info(
            f"HeaderFooterCleaner: Detected repeated lines: {len(lines_to_remove)}, "
            f"Removed: {removed_count} lines"
        )

        return '\n'.join(cleaned_lines)

    def _find_headers_and_footers(self, lines: list[str]) -> set[str]:
        """Find normalized lines that are headers/footers.

        Args:
            lines: Original text lines.

        Returns:
            Set of normalized lines identified as headers/footers.
        """
        # Normalize and count line frequencies
        line_frequencies = Counter()
        normalized_to_original = {}

        for line in lines:
            normalized = self._normalize_line(line.strip())
            if normalized:
                line_frequencies[normalized] += 1
                normalized_to_original[normalized] = line.strip()

        # Find candidates
        candidates_to_remove = set()

        for normalized_line, frequency in line_frequencies.items():
            if frequency < self.min_frequency:
                continue

            # Check if this line is a header/footer candidate
            if self._is_header_footer_candidate(normalized_line):
                candidates_to_remove.add(normalized_line)
                logger.debug(
                    f"HeaderFooterCleaner: Candidate '{normalized_line[:60]}' "
                    f"(appeared {frequency} times)"
                )

        return candidates_to_remove

    def _normalize_line(self, line: str) -> str:
        """Normalize a line for frequency comparison.

        Args:
            line: Raw line text.

        Returns:
            Normalized line (or empty string if it should be ignored).
        """
        # Strip whitespace
        normalized = line.strip()

        if not normalized:
            return ""

        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)

        # Normalize unicode spaces
        normalized = re.sub(r'[\u00A0\u2000-\u200B\u3000]', ' ', normalized)

        return normalized

    def _is_header_footer_candidate(self, line: str) -> bool:
        """Check if a line looks like a header or footer.

        Uses multiple heuristics to identify non-content lines.

        Args:
            line: Normalized line text.

        Returns:
            True if line appears to be a header/footer.
        """
        # Filter out empty lines
        if len(line) < 2:
            return False

        # Filter out pure numbers (page numbers handled by PageNumberCleaner)
        if self._pure_number.match(line):
            return False

        # Check length constraints
        if len(line) > self.max_line_length:
            return False

        # Check word count
        words = line.split()
        if len(words) == 0 or len(words) > self.max_line_words:
            return False

        # IMPORTANT: Lines ending with periods are usually content, not headers
        # (headers/footers typically don't end with periods)
        if self._ends_with_period.search(line):
            return False

        # If we get here, it looks like a header/footer
        return True

    def _looks_like_paragraph(self, line: str, words: list[str]) -> bool:
        """Check if a line looks like part of a paragraph.

        Args:
            line: Normalized line.
            words: Split words.

        Returns:
            True if line appears to be paragraph content.
        """
        # Very long lines with many words are usually content
        if len(line) > 60 and len(words) > 8:
            return True

        # Lines that end with common sentence punctuation are usually content
        if line.endswith('.') or line.endswith('?') or line.endswith('!'):
            if len(words) > 5:
                return True

        return False

    def _has_reasonable_char_distribution(self, line: str) -> bool:
        """Check if character distribution is reasonable for header/footer.

        Args:
            line: Line text.

        Returns:
            True if character distribution looks reasonable.
        """
        # Count special characters (very lenient check)
        special_chars = len(self._special_char_ratio.findall(line))
        total_chars = len(line)

        # Only reject if it's mostly special characters (e.g., corrupted)
        if special_chars > total_chars * 0.6:
            return False

        return True