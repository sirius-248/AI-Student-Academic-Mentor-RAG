"""Command-line interface for the AI Student Academic Mentor RAG system."""
from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from app.pipeline import (
    PipelineConfigurationError,
    PipelineGenerationError,
    PipelineIndexingError,
    PipelineValidationError,
    RAGPipeline,
)

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure the CLI's application logging."""
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def find_pdf_path(directory: Path) -> Path:
    """Return the first PDF in ``directory`` or raise a helpful error."""
    if not directory.is_dir():
        raise FileNotFoundError(f"PDF directory not found: {directory}")
    pdf_files = sorted(directory.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in: {directory}")
    return pdf_files[0]


def create_document_id(pdf_path: Path) -> str:
    """Create a predictable identifier from a source filename."""
    identifier = re.sub(r"[^a-z0-9]+", "_", pdf_path.stem.lower()).strip("_")
    return identifier or "document"


def _display_indexing_result(result: object) -> None:
    """Print the stable, user-facing indexing summary."""
    pages = getattr(result, "pages_processed", None)
    print("\nIndexed:")
    print(getattr(result, "document_name", "Unknown document"))
    print(f"Document ID: {getattr(result, 'document_id', 'unknown')}")
    print(f"Pages processed: {pages if pages is not None else 'N/A'}")
    print(f"Chunks created: {getattr(result, 'chunks_created', 0)}")
    print(f"Vectors added: {getattr(result, 'vectors_added', 0)}")
    print(f"Processing time: {getattr(result, 'processing_time_ms', 0.0) / 1000:.2f} s")


def _display_answer(response: object) -> None:
    """Print an answer and its source citations."""
    print("\n" + "-" * 36)
    print("Answer")
    print("-" * 36)
    print(getattr(response, "answer", ""))
    print("\n" + "-" * 36)
    print("Sources")
    print("-" * 36)
    sources = getattr(response, "sources", ())
    if not sources:
        print("No matching sources were found.")
    else:
        for source in sources:
            page = getattr(source, "page_number", None)
            location = f" (Page {page})" if page is not None else ""
            print(f"{getattr(source, 'filename', 'Unknown source')}{location}")
    print(f"\nResponse Time:\n{getattr(response, 'total_time_ms', 0.0) / 1000:.2f} s")


def main() -> int:
    """Index the configured document and serve an interactive RAG session."""
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")
    configure_logging()

    configured_directory = Path(os.getenv("PDF_DATA_PATH", "data/sample_pdfs"))
    pdf_directory = configured_directory if configured_directory.is_absolute() else project_root / configured_directory

    try:
        pdf_path = find_pdf_path(pdf_directory)
        document_id = create_document_id(pdf_path)
        logger.info("Initializing RAG pipeline")
        pipeline = RAGPipeline()
        logger.info("Indexing PDF: %s", pdf_path.name)
        # The current facade accepts the path first and the optional ID by name.
        result = pipeline.index_document(pdf_path, document_id=document_id)
        _display_indexing_result(result)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        print(f"\nUnable to start: {exc}")
        return 1
    except PipelineValidationError as exc:
        logger.error("Invalid indexing request: %s", exc)
        print(f"\nUnable to index the document: {exc}")
        return 1
    except (PipelineConfigurationError, PipelineIndexingError) as exc:
        logger.error("Indexing failed: %s", exc)
        print("\nUnable to index the document. Check the logs and configuration, then try again.")
        return 1
    except KeyboardInterrupt:
        print("\nGoodbye.")
        return 0

    print("\n" + "=" * 51)
    print("AI Student Academic Mentor")
    print("=" * 51)
    print("Ask a question, or type 'exit' or 'quit' to finish.")

    while True:
        try:
            question = input("\nAsk a question\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0

        if question.lower() in {"exit", "quit"}:
            print("Goodbye.")
            return 0
        if not question:
            print("Please enter a question or type 'exit'.")
            continue

        try:
            _display_answer(pipeline.answer_question(question))
        except PipelineValidationError as exc:
            print(f"Unable to process that question: {exc}")
        except PipelineGenerationError as exc:
            logger.error("Question answering failed: %s", exc)
            print("Unable to generate an answer right now. Please try again.")
        except KeyboardInterrupt:
            print("\nGoodbye.")
            return 0


if __name__ == "__main__":
    sys.exit(main())
