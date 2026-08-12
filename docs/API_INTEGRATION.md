# API integration

For React-specific integration, including TypeScript examples, CORS setup, source rendering, loading states, and error handling, see [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md).

Start the backend from the repository root after installing `requirements.txt`:

```powershell
python -m uvicorn app.api.main:app --reload
```

Swagger is at `http://127.0.0.1:8000/docs`; the OpenAPI document is at `/openapi.json`.

React flow: upload a PDF, retain the returned `document_id`, then send that ID with each question. Set `API_CORS_ORIGINS` to the React development/production origins.

`POST /api/v1/documents/upload` accepts `multipart/form-data` with `file` (PDF), and optional `document_id`, `course_id`, and `user_id`.

```js
const form = new FormData();
form.append('file', pdfFile);
form.append('course_id', 'bcs602');
const upload = await fetch('http://127.0.0.1:8000/api/v1/documents/upload', {
  method: 'POST', body: form,
});
const document = await upload.json();
// { document_id, filename, indexing_status, pages_processed,
//   chunks_created, vectors_added, processing_time_ms }
```

`POST /api/v1/questions/ask` accepts JSON:

```js
const response = await fetch('http://127.0.0.1:8000/api/v1/questions/ask', {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ document_id: document.document_id, question }),
});
const answer = await response.json();
// { document_id, question, answer, sources, retrieval_time_ms,
//   generation_time_ms, total_time_ms, model_name }
```

`GET /api/v1/health` returns `{ "status": "ok", "service": "ai-student-academic-mentor" }` without constructing the RAG pipeline.

Expected errors use `{ "error": { "code", "message" } }`: 400 invalid file/request, 404 unknown or unindexed document, 413 oversized PDF, 422 invalid JSON/form data, 503 temporarily unavailable answer service, and 500 unexpected/indexing failure.
