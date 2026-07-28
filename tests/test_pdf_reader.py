import tempfile
from pathlib import Path

from PyPDF2 import PdfWriter

from app.document_reader.pdf_reader import PDFReader


def test_pdf_reader_raises_for_pdf_without_text() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "test_document.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with pdf_path.open("wb") as output_file:
            writer.write(output_file)

        reader = PDFReader(str(pdf_path))
        try:
            reader.read()
            assert False, "Expected ValueError when PDF contains no extractable text"
        except ValueError as exc:
            assert "No extractable text" in str(exc)
