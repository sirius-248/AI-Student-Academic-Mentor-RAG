"""Line merger for repairing PDF line breaks."""

import logging
import re

from .base_cleaner import BaseCleaner

logger = logging.getLogger(__name__)


class LineMerger(BaseCleaner):
    """Repair PDF line breaks by merging broken sentences.

    Detects lines that are artificially broken within a sentence and merges
    them back together, while preserving paragraph structure, lists, and headings.

    Also handles orphan words (1-2 word lines that are continuations).
    """

    # Sentence-ending punctuation
    SENTENCE_ENDINGS = {'.', '?', '!', ':', ';'}

    # Characters that typically start a new line item
    NEW_LINE_MARKERS = {'•', '-', '*'}

    # Patterns that indicate a new section/list
    NEW_SECTION_PATTERNS = [
        r'^Chapter\s+\d+',
        r'^Section\s+\d+',
        r'^\d+\.',  # Numbered list
        r'^\d+\)',  # Numbered list alternative
    ]

    def __init__(self) -> None:
        """Initialize line merger."""
        # Compile regex patterns once
        self._section_patterns = [
            re.compile(pattern) for pattern in self.NEW_SECTION_PATTERNS
        ]
        self._is_orphan_word = re.compile(r'^[a-zA-Z\s]{1,30}$')

    def clean(self, text: str) -> str:
        """Merge lines that are broken within sentences.

        Args:
            text: Input text with potential line breaks.

        Returns:
            Text with merged lines.
        """
        lines = text.split('\n')
        merged_lines = []
        i = 0

        while i < len(lines):
            current_line = lines[i]

            # If this is the last line, just add it
            if i == len(lines) - 1:
                merged_lines.append(current_line)
                i += 1
                continue

            next_line = lines[i + 1]

            # Check if current and next lines should be merged
            if self._should_merge(current_line, next_line):
                # Merge with appropriate spacing
                merged = self._merge_lines(current_line, next_line)
                logger.debug(f"Merged: '{current_line[:40]}...' + '{next_line[:40]}...'")
                merged_lines.append(merged)
                i += 2
            else:
                merged_lines.append(current_line)
                i += 1

        return '\n'.join(merged_lines)

    def _should_merge(self, current_line: str, next_line: str) -> bool:
        """Check if two consecutive lines should be merged.

        Args:
            current_line: Current line.
            next_line: Next line.

        Returns:
            True if lines should be merged.
        """
        current_stripped = current_line.rstrip()
        next_stripped = next_line.lstrip()

        # Don't merge if either line is empty
        if not current_stripped or not next_stripped:
            return False

        # SPECIAL CASE: Orphan words (1-2 word lines that are continuations)
        # Check this FIRST before other restrictions
        if self._is_orphan_continuation(current_stripped, next_stripped):
            return True

        # Don't merge if next line starts with a list marker
        if next_stripped and next_stripped[0] in self.NEW_LINE_MARKERS:
            return False

        # Don't merge if next line is a numbered list
        if re.match(r'^\d+[\.)]', next_stripped):
            return False

        # Don't merge if next line is a section heading
        for pattern in self._section_patterns:
            if pattern.match(next_stripped):
                return False

        # Don't merge if current line appears to be a heading
        if self._is_heading(current_stripped):
            return False

        # Don't merge if next line appears to be a heading
        if self._is_heading(next_stripped):
            return False

        # Don't merge if current line ends with sentence-ending punctuation
        if current_stripped[-1] in self.SENTENCE_ENDINGS:
            return False

        return True

    def _is_orphan_continuation(self, current_line: str, next_line: str) -> bool:
        """Check if next line is an orphan word that should be merged.

        Detects isolated words (1-2 words) that are continuations of the previous line.

        Args:
            current_line: Current line.
            next_line: Next line.

        Returns:
            True if next line is an orphan continuation.
        """
        # Check if next line is very short (1-3 words)
        next_words = next_line.split()
        if len(next_words) > 3:
            return False

        # Next line should be only letters and spaces (looks like word continuation)
        if not self._is_orphan_word.match(next_line):
            return False

        # Current line should NOT end with sentence-ending punctuation
        current_stripped = current_line.rstrip()
        if current_stripped[-1] in self.SENTENCE_ENDINGS:
            return False

        # Current line should look like it's mid-sentence
        # (multiple words suggest it might be a complete thought without period)
        current_words = current_stripped.split()
        if len(current_words) < 2:
            return False

        # Next line should not start with a capital letter (suggests new sentence)
        # unless current line ends with a colon or similar
        if next_line and next_line[0].isupper():
            if current_stripped and current_stripped[-1] not in (':', '-'):
                # Might be a new sentence, don't merge
                return False

        logger.debug(f"Detected orphan word: '{next_line}'")
        return True

    def _merge_lines(self, current_line: str, next_line: str) -> str:
        """Merge two lines with appropriate spacing.

        Args:
            current_line: Current line.
            next_line: Next line.

        Returns:
            Merged line.
        """
        current_stripped = current_line.rstrip()
        next_stripped = next_line.lstrip()

        # Add space between if current doesn't end with space/hyphen
        if current_stripped and not current_stripped[-1] in (' ', '-'):
            return current_stripped + ' ' + next_stripped
        else:
            return current_stripped + next_stripped

    def _is_heading(self, line: str) -> bool:
        """Check if a line looks like a heading.

        Args:
            line: Line to check.

        Returns:
            True if line appears to be a heading.
        """
        # Too long to be a typical heading
        if len(line) > 80:
            return False

        # Very short lines might be headings
        if len(line) < 4:
            return True

        # Check for title case or all caps with reasonable length
        words = line.split()
        if len(words) == 0:
            return False

        if len(words) <= 5:
            # All caps or title case (multiple capitalized words)
            if line.isupper():
                return True
            # Title case: multiple words starting with capital
            capitalized_count = sum(1 for w in words if w and w[0].isupper())
            if capitalized_count >= len(words) * 0.6:
                return True

        return False
