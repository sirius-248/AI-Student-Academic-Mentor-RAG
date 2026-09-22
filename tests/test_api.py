from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.config import APISettings
from app.api.dependencies import RegisteredDocument
from app.api.main import create_app
from app.models.document_chunk import DocumentChunk
from app.pipeline import AnswerResponse, DocumentMetadata, IndexingResult, SourceReference, RAGPipeline
from app.pipeline.config import PipelineConfig
from app.retriever.retriever import Retriever
from app.vector_store.config import VECTOR_STORE_DIR, INDEX_FILENAME, METADATA_FILENAME
from app.vector_store.faiss_vector_store import FAISSVectorStore


class FakePipeline:
    def index_document(self, path, document_id=None):
        return IndexingResult(
            DocumentMetadata(document_id, Path(path).name, str(path), page_count=3),
            chunks_created=4, vectors_added=4, processing_time_ms=12.5,
        )

    def answer_question(self, question, *, top_k=None, document_ids=None):
        return AnswerResponse(
            answer="Supervised and unsupervised learning are types of machine learning.",
            sources=(SourceReference(document_ids[0], "module.pdf", 12, 0.91, 3),),
            retrieval_time_ms=2.0, generation_time_ms=10.0, total_time_ms=12.0,
            prompt_context_length=100, chunk_count=1, model_name="fake-model",
        )


class DummyEmbeddingService:
    def embed_query(self, query):
        return [1.0, 0.0, 0.0]


class RecordingVectorStore:
    def __init__(self):
        self.seen_document_ids = None

    def search(self, query_embedding, top_k=5, document_ids=None):
        self.seen_document_ids = document_ids
        return []


class RecordingRetriever:
    def __init__(self):
        self.seen_document_ids = None

    def retrieve_context(self, query, top_k=None, min_score=None, document_ids=None):
        self.seen_document_ids = document_ids
        return SimpleNamespace(results=[], retrieval_time_ms=0.0, top_k=top_k, query=query)


def make_client(tmp_path):
    app = create_app(APISettings(upload_dir=tmp_path / "uploads", max_upload_size_mb=1))
    app.state.pipeline = FakePipeline()
    return TestClient(app)


def test_health_does_not_initialize_pipeline(tmp_path):
    app = create_app(APISettings(upload_dir=tmp_path / "uploads"))
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-student-academic-mentor"}
    assert not hasattr(app.state, "pipeline")


def test_cors_allows_configured_react_origin(tmp_path):
    app = create_app(APISettings(upload_dir=tmp_path / "uploads", cors_origins=("http://localhost:5173",)))
    response = TestClient(app).options(
        "/api/v1/questions/ask",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_invalid_question_is_rejected(tmp_path):
    response = make_client(tmp_path).post("/api/v1/questions/ask", json={"document_id": "doc", "question": "   "})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_missing_document_is_not_found(tmp_path):
    response = make_client(tmp_path).post("/api/v1/questions/ask", json={"document_id": "missing", "question": "What is ML?"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_invalid_file_type_is_rejected(tmp_path):
    response = make_client(tmp_path).post("/api/v1/documents/upload", files={"file": ("notes.txt", b"text", "text/plain")})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_oversized_upload_is_rejected(tmp_path):
    app = create_app(APISettings(upload_dir=tmp_path / "uploads", max_upload_size_mb=1))
    app.state.pipeline = FakePipeline()
    response = TestClient(app).post("/api/v1/documents/upload", files={"file": ("large.pdf", b"%PDF-" + b"x" * (1024 * 1024 + 1), "application/pdf")})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_upload_indexes_with_mocked_pipeline(tmp_path):
    response = make_client(tmp_path).post(
        "/api/v1/documents/upload",
        data={"document_id": "bcs602-module-1", "course_id": "bcs602"},
        files={"file": ("module.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["document_id"] == "bcs602-module-1"
    assert body["filename"] == "module.pdf"
    assert body["chunks_created"] == 4


def test_question_uses_mocked_pipeline(tmp_path):
    client = make_client(tmp_path)
    client.app.state.document_registry.register(RegisteredDocument("doc", "module.pdf", tmp_path / "module.pdf", indexed=True))
    response = client.post("/api/v1/questions/ask", json={"document_id": "doc", "question": "What are the types of machine learning?"})
    assert response.status_code == 200
    body = response.json()
    assert body["model_name"] == "fake-model"
    assert body["sources"][0]["page_number"] == 12


def test_fresh_startup_with_no_vector_store(tmp_path, monkeypatch):
    vector_store_dir = tmp_path / "vector_store"
    monkeypatch.setattr("app.vector_store.config.VECTOR_STORE_DIR", vector_store_dir)
    monkeypatch.setattr("app.vector_store.config.INDEX_FILENAME", "index.faiss")
    monkeypatch.setattr("app.vector_store.config.METADATA_FILENAME", "metadata.pkl")

    app = create_app(APISettings(upload_dir=tmp_path / "uploads", max_upload_size_mb=1))

    assert hasattr(app.state, "vector_store")
    assert app.state.vector_store.is_empty()
    assert app.state.document_registry.get("doc-1") is None


def test_startup_with_persisted_faiss_metadata_recovers_registry(tmp_path, monkeypatch):
    vector_store_dir = tmp_path / "vector_store"
    monkeypatch.setattr("app.vector_store.config.VECTOR_STORE_DIR", vector_store_dir)
    monkeypatch.setattr("app.vector_store.config.INDEX_FILENAME", "index.faiss")
    monkeypatch.setattr("app.vector_store.config.METADATA_FILENAME", "metadata.pkl")

    store = FAISSVectorStore(embedding_dim=3)
    chunk = DocumentChunk(
        document_id="doc-1",
        chunk_id=1,
        text="Machine learning is a field of study.",
        source_file="module.pdf",
        page_number=1,
        embedding=[1.0, 0.0, 0.0],
    )
    store.add_documents([chunk])
    store.save(directory=vector_store_dir)

    app = create_app(APISettings(upload_dir=tmp_path / "uploads", max_upload_size_mb=1))
    reconstructed = app.state.document_registry.get("doc-1")

    assert reconstructed is not None
    assert reconstructed.document_id == "doc-1"
    assert reconstructed.filename == "module.pdf"
    assert reconstructed.local_path == tmp_path / "uploads" / "doc-1_module.pdf"
    assert reconstructed.indexed is True


def test_question_after_simulated_restart_uses_persisted_state(tmp_path, monkeypatch):
    vector_store_dir = tmp_path / "vector_store"
    monkeypatch.setattr("app.vector_store.config.VECTOR_STORE_DIR", vector_store_dir)
    monkeypatch.setattr("app.vector_store.config.INDEX_FILENAME", "index.faiss")
    monkeypatch.setattr("app.vector_store.config.METADATA_FILENAME", "metadata.pkl")

    store = FAISSVectorStore(embedding_dim=3)
    chunk = DocumentChunk(
        document_id="doc-1",
        chunk_id=1,
        text="Machine learning is a field of study.",
        source_file="module.pdf",
        page_number=1,
        embedding=[1.0, 0.0, 0.0],
    )
    store.add_documents([chunk])
    store.save(directory=vector_store_dir)

    app = create_app(APISettings(upload_dir=tmp_path / "uploads", max_upload_size_mb=1))
    app.state.pipeline = FakePipeline()

    client = TestClient(app)
    response = client.post("/api/v1/questions/ask", json={"document_id": "doc-1", "question": "What is machine learning?"})

    assert response.status_code == 200
    assert response.json()["document_id"] == "doc-1"
    assert response.json()["answer"] == "Supervised and unsupervised learning are types of machine learning."


def test_faiss_vectorstore_document_id_filtering_isolates_results(tmp_path):
    store = FAISSVectorStore(embedding_dim=3)
    store.add_documents([
        DocumentChunk(document_id="doc-A", chunk_id=1, text="doc A chunk", source_file="a.pdf", page_number=1, embedding=[1.0, 0.0, 0.0]),
        DocumentChunk(document_id="doc-B", chunk_id=1, text="doc B chunk", source_file="b.pdf", page_number=1, embedding=[0.0, 1.0, 0.0]),
    ])

    results = store.search(query_embedding=[1.0, 0.0, 0.0], top_k=2, document_ids=["doc-A"])

    assert len(results) == 1
    assert all(result.chunk.document_id == "doc-A" for result in results)


def test_faiss_document_aware_search_keeps_id_and_embedding_aligned_when_embedding_is_missing():
    store = FAISSVectorStore(embedding_dim=3)
    store._metadata_map = {
        0: DocumentChunk(document_id="doc-A", chunk_id=1, text="missing embedding", source_file="a.pdf", page_number=1, embedding=None),
        1: DocumentChunk(document_id="doc-A", chunk_id=2, text="valid embedding", source_file="a.pdf", page_number=2, embedding=[1.0, 0.0, 0.0]),
    }
    store._vector_count = 2

    results = store.search(query_embedding=[1.0, 0.0, 0.0], top_k=2, document_ids=["doc-A"])

    assert len(results) == 1
    assert results[0].chunk.chunk_id == 2
    assert results[0].chunk.embedding == [1.0, 0.0, 0.0]


def test_retiever_propagates_document_ids_to_vector_store():
    vector_store = RecordingVectorStore()
    retriever = Retriever(embedding_service=DummyEmbeddingService(), vector_store=vector_store)

    retriever.retrieve_context("question", top_k=3, document_ids=["doc-A"])

    assert vector_store.seen_document_ids == ["doc-A"]


def test_rag_pipeline_propagates_document_ids_to_retriever():
    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline._validated_question = staticmethod(lambda value: value.strip())
    pipeline._validated_document_ids = staticmethod(lambda value: frozenset(value))
    pipeline._context_with_results = staticmethod(lambda context, results: context)
    pipeline._prompt_request = staticmethod(lambda question, context: SimpleNamespace(question=question, retrieved_context=context))
    pipeline._source_references = staticmethod(lambda results: ())
    pipeline._retriever = RecordingRetriever()
    pipeline._prompt_builder = type("PB", (), {"build_prompt": lambda self, request: SimpleNamespace(full_prompt="answer", context_length=0, chunk_count=0)})()
    pipeline._gemini_client = type("GC", (), {"generate": lambda self, prompt: "answer", "model": "fake"})()
    pipeline._config = type("C", (), {"default_top_k": 5})()

    pipeline.answer_question("What is machine learning?", document_ids=["doc-A"])

    assert pipeline._retriever.seen_document_ids == frozenset({"doc-A"})


def test_preserve_global_behavior_when_document_ids_is_none(tmp_path):
    store = FAISSVectorStore(embedding_dim=3)
    store.add_documents([
        DocumentChunk(document_id="doc-A", chunk_id=1, text="doc A chunk", source_file="a.pdf", page_number=1, embedding=[1.0, 0.0, 0.0]),
        DocumentChunk(document_id="doc-B", chunk_id=1, text="doc B chunk", source_file="b.pdf", page_number=1, embedding=[0.0, 1.0, 0.0]),
    ])

    results = store.search(query_embedding=[1.0, 0.0, 0.0], top_k=5)

    assert len(results) == 2
    assert {result.chunk.document_id for result in results} == {"doc-A", "doc-B"}
