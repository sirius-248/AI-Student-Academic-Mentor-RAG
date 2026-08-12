# Future external document integration

No PostgreSQL or external document system is integrated by this RAG service today. The current upload endpoint saves a PDF locally, records its status in the development-only in-memory registry, then calls `RAGPipeline.index_document(path, document_id=...)`.

The future boundary is:

```text
Shashank's PDF/database system
        |
document_id
        |
PDF location, download API, or storage reference
        |
FastAPI document adapter
        |
RAGPipeline.index_document(pdf_path, document_id=...)
        |
FAISS
```

The exact adapter will be selected only after Shashank provides the real document API, storage mechanism, and metadata contract. It may obtain a document from a local path, object-storage key, authenticated download URL, or another service API. No database schema, table name, storage layout, or credentials are assumed here.

`DocumentRegistry` already isolates API routes from document-record storage. A future integration can replace `InMemoryDocumentRegistry` with a repository backed by Shashank's service/database, and can add a small document-source adapter that resolves `document_id` to a temporary/local PDF path. Neither change should modify `RAGPipeline`, whose contract remains a PDF path plus optional `document_id`.

The RAG system should receive the resolved PDF location and stable document ID; it should not receive database sessions, database models, PDF bytes stored in PostgreSQL, or application schema concerns.
