# Data Directory

## sample_pdfs

Place your PDF documents in the `sample_pdfs/` directory. These documents will be used by the RAG system to provide context-aware answers to student queries.

### Example Usage

```python
from app.document_reader.pdf_reader import PDFReader

pdf_reader = PDFReader("data/sample_pdfs/your_document.pdf")
content = pdf_reader.read()
```
