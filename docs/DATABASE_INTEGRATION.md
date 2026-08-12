# PostgreSQL integration boundary

RAG remains independent of application storage: PDF file path → preprocessing → chunks → embeddings → FAISS → retrieval → prompt → Gemini. `RAGPipeline` should not receive a database session or write application records.

The API currently uses `DocumentRegistry` with `InMemoryDocumentRegistry`. Replace that implementation with `PostgresDocumentRegistry` (and inject it through `app.state`) without changing API routes or `RAGPipeline`.

PostgreSQL should store users, courses, document/upload metadata (document ID, original filename, object-storage key/local development path, ownership, status, timestamps), and chat/conversation history. It should not store PDF bytes, embedding vectors, FAISS index files, raw prompts, or Gemini credentials. Store PDFs in local development storage and later object/cloud storage; keep FAISS persistence under the vector-store configuration.

The current FAISS store is a shared index. `answer_question(..., document_ids=[id])` filters retrieved chunks after the similarity search. This prevents returned citations from another document but can reduce recall when many documents share an index. A future vector store should support metadata filtering at search time or maintain safely isolated indexes before relying on multi-document production retrieval.
