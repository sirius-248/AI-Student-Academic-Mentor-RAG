"""Application entry point for the AI Student Academic Mentor."""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from chunking.text_chunker import TextChunker
from document_reader.pdf_reader import PDFReader
from llm.base_client import LLMClientError
from llm.client_factory import LLMClientFactory
from models.document_chunk import DocumentChunk
from preprocessing.pipeline import PreprocessingPipeline
from prompts.prompts import PromptManager


def configure_logging() -> None:
    """Configure application logging."""

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def find_pdf_path(directory: Path) -> Path:
    """Return the first PDF found inside the given directory."""

    pdf_files = sorted(directory.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in: {directory}"
        )

    return pdf_files[0]


def save_chunks(chunks: list[DocumentChunk], output_file: Path) -> None:
    """
    Save all generated chunks to a text file with metadata.

    Each chunk includes its ID, document ID, source file, and optional page number.
    """

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write("=" * 80 + "\n")
            file.write(f"Chunk ID : {chunk.chunk_id}\n")
            file.write(f"Document : {chunk.document_id}\n")
            file.write(f"Source   : {chunk.source_file}\n")
            if chunk.page_number is not None:
                file.write(f"Page     : {chunk.page_number}\n")
            file.write("=" * 80 + "\n")
            file.write(chunk.text)
            file.write("\n\n")


def main() -> None:
    """Run the AI Student Academic Mentor pipeline."""

    project_root = Path(__file__).resolve().parents[1]

    load_dotenv(project_root / ".env")

    configure_logging()
    logger = logging.getLogger(__name__)

    pdf_folder = Path(
        os.getenv(
            "PDF_DATA_PATH",
            project_root / "data" / "sample_pdfs",
        )
    )

    try:
        logger.info("Reading PDF...")

        pdf_path = find_pdf_path(pdf_folder)

        reader = PDFReader()
        document_text = reader.extract_text(str(pdf_path))

        logger.info("Preprocessing text...")

        pipeline = PreprocessingPipeline()
        clean_text = pipeline.execute(document_text)

        logger.info("Chunking document...")

        chunker = TextChunker(
            chunk_size=1000,
            overlap=200,
        )

        chunks = chunker.chunk_text(
            text=clean_text,
            source_file=pdf_path.name,
        )

        logger.info("Created %d chunks.", len(chunks))

        if not chunks:
            raise ValueError("No chunks were generated from the document.")

        save_chunks(
            chunks,
            project_root / "output" / "chunks.txt",
        )

        logger.info("Chunks saved to output/chunks.txt")

        logger.info("Generating prompt...")

        # Temporary: only use the first chunk
        prompt = PromptManager.create_summary_prompt(chunks[0].text)

        logger.info("Initializing LLM...")

        client = LLMClientFactory.create_client()

        logger.info("Generating response...")

        response = client.generate(prompt)

        print("\n")
        print("=" * 80)
        print(response)
        print("=" * 80)

    except (
        FileNotFoundError,
        ValueError,
        LLMClientError,
    ) as exc:

        logger.error(str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()