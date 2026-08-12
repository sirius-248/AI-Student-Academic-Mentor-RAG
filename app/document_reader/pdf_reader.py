"""PDF Reader module for processing PDF documents."""

import logging
from pathlib import Path
from typing import List, Optional

from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


class PDFReader:
    """Handle PDF document reading and processing."""

    def __init__(self, file_path: Optional[str] = None) -> None:
        """Initialize the PDF reader.

        Args:
            file_path: Optional path to the PDF file.
        """
        self.file_path = Path(file_path) if file_path else None

    def extract_text(self, file_path: Optional[str] = None) -> str:
        """Extract text from a PDF file.

        Args:
            file_path: Optional PDF path. If omitted, uses the configured path.

        Returns:
            Extracted document text.

        Raises:
            FileNotFoundError: If the file cannot be found.
            ValueError: If the file is not a PDF or contains no text.
        """
        path = Path(file_path) if file_path else self.file_path
        if path is None:
            raise ValueError("PDF file path is required.")
        # Retain an explicitly supplied path so page-oriented operations can
        # subsequently use the same reader instance.
        self.file_path = path

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Invalid file type: {path.suffix}. Only PDF files are supported."
            )

        try:
            with path.open("rb") as file_handle:
                reader = PdfReader(file_handle)
                if not reader.pages:
                    raise ValueError("The PDF contains no pages.")

                pages: List[str] = []
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    pages.append(page_text)

                document_text = "\n".join(text for text in pages if text).strip()

        except Exception as exc:
            logger.exception("Failed to extract text from PDF: %s", path)
            raise ValueError(f"Unable to extract text from PDF: {path}") from exc

        if not document_text:
            raise ValueError("No extractable text was found in the PDF.")

        return document_text

    def read(self) -> str:
        """Read the configured PDF file and return its text."""
        if self.file_path is None:
            raise ValueError("PDF file path must be configured before calling read().")
        return self.extract_text(str(self.file_path))

    def extract_pages(self) -> List[str]:
        """Return the raw text for each page in the configured PDF."""
        if self.file_path is None:
            raise ValueError("PDF file path must be configured before calling extract_pages().")

        with self.file_path.open("rb") as file_handle:
            reader = PdfReader(file_handle)
            return [page.extract_text() or "" for page in reader.pages]
