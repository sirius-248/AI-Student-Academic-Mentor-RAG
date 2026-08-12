from pathlib import Path

from fastapi.testclient import TestClient

from app.api.config import APISettings
from app.api.dependencies import RegisteredDocument
from app.api.main import create_app
from app.pipeline import AnswerResponse, DocumentMetadata, IndexingResult, SourceReference


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
