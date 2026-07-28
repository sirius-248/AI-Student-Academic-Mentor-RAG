"""Preprocessing pipeline orchestration."""

import logging

from .base_cleaner import BaseCleaner
from .pdf_cleaner import PDFCleaner
from .watermark_cleaner import WatermarkCleaner
from .header_footer_cleaner import HeaderFooterCleaner
from .page_number_cleaner import PageNumberCleaner
from .line_merger import LineMerger
from .whitespace_cleaner import WhitespaceCleaner

logger = logging.getLogger(__name__)


class PreprocessingPipeline:
    """Orchestrates a sequence of text cleaning operations.

    Executes cleaners in a specific order optimized for preprocessing
    PDF-extracted text for RAG applications.

    Execution order:
    1. PDFCleaner - normalize raw text
    2. WatermarkCleaner - remove watermarks
    3. HeaderFooterCleaner - remove repeated headers/footers
    4. PageNumberCleaner - remove page numbers
    5. LineMerger - repair broken lines
    6. WhitespaceCleaner - final normalization
    """

    def __init__(self, cleaners: list[BaseCleaner] | None = None) -> None:
        """Initialize preprocessing pipeline.

        Args:
            cleaners: Optional list of cleaners to use. If not provided,
                     uses the default pipeline in the recommended order.
        """
        if cleaners is None:
            self.cleaners = self._default_cleaners()
        else:
            self.cleaners = cleaners

        logger.info(f"Preprocessing pipeline initialized with {len(self.cleaners)} cleaners")

    @staticmethod
    def _default_cleaners() -> list[BaseCleaner]:
        """Create the default preprocessing pipeline.

        Returns:
            List of cleaners in optimal order.
        """
        return [
            PDFCleaner(),
            WatermarkCleaner(),
            HeaderFooterCleaner(),
            PageNumberCleaner(),
            LineMerger(),
            WhitespaceCleaner(),
        ]

    def execute(self, text: str) -> str:
        """Execute all cleaners in sequence.

        Args:
            text: Raw text to process.

        Returns:
            Cleaned and normalized text.
        """
        result = text
        for cleaner in self.cleaners:
            cleaner_name = cleaner.__class__.__name__
            logger.debug(f"Executing {cleaner_name}...")
            result = cleaner.clean(result)

        logger.info("Preprocessing pipeline completed")
        return result