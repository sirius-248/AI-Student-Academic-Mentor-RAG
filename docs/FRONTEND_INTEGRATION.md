# React frontend integration

## Run the backend

From the repository root, install the Python dependencies and start the API:

```powershell
python -m uvicorn app.api.main:app --reload
```

The local API base URL is `http://127.0.0.1:8000`. Swagger is available at `http://127.0.0.1:8000/docs` and the OpenAPI specification is at `http://127.0.0.1:8000/openapi.json`.

Before starting the backend, configure the React development origin in `.env`. The default supports Create React App and Vite:

```dotenv
API_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

For another local frontend port, add its exact origin to this comma-separated setting and restart the backend. The API intentionally does not use wildcard origins because browser credentials are enabled.

## Frontend flow

1. Upload the selected PDF.
2. Store `data.document_id` from the successful upload response in React state (and, if needed, your frontend session state).
3. Send that ID with every question for the selected document.
4. Render `data.answer`, sources, and optional timing information.

`document_id` is the document identity. Do not derive it from the filename or substitute a Swagger placeholder such as `"string"`.

## Health check

`GET /api/v1/health` returns:

```json
{
  "status": "ok",
  "service": "ai-student-academic-mentor"
}
```

This endpoint does not initialize the embedding model or Gemini.

## Upload a document

`POST /api/v1/documents/upload` accepts `multipart/form-data`.

Required field: `file` (a PDF). Optional integration fields: `document_id`, `course_id`, and `user_id`. If `document_id` is omitted, the API generates one. Never manually set the `Content-Type` header when sending `FormData`; the browser supplies the multipart boundary.

```ts
const API_BASE_URL = "http://127.0.0.1:8000";

export async function uploadDocument(
  file: File,
  options?: { documentId?: string; courseId?: string; userId?: string },
) {
  const formData = new FormData();
  formData.append("file", file);

  if (options?.documentId) formData.append("document_id", options.documentId);
  if (options?.courseId) formData.append("course_id", options.courseId);
  if (options?.userId) formData.append("user_id", options.userId);

  const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  if (!response.ok) throw new Error(data.error?.message ?? "Upload failed");
  return data;
}
```

Successful (`201`) response:

```json
{
  "document_id": "bcs602-module-1",
  "filename": "BCS602-module-1-pdf.pdf",
  "indexing_status": "indexed",
  "pages_processed": null,
  "chunks_created": 24,
  "vectors_added": 24,
  "processing_time_ms": 840.2,
  "course_id": "bcs602",
  "user_id": "student-123"
}
```

`pages_processed` is `null` if the active PDF reader did not provide a page count. Do not invent a page count in the UI.

## Ask a question

`POST /api/v1/questions/ask` accepts JSON. `document_id` must be the value returned from upload.

```ts
export async function askQuestion(documentId: string, question: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/questions/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, question }),
  });

  const data = await response.json();
  if (!response.ok) throw new Error(data.error?.message ?? "Unable to answer question");
  return data;
}
```

Successful (`200`) response contains only fields supplied by the existing RAG answer DTO:

```json
{
  "document_id": "bcs602-module-1",
  "question": "What are the types of machine learning?",
  "answer": "...",
  "sources": [
    {
      "document_id": "bcs602-module-1",
      "filename": "BCS602-module-1-pdf.pdf",
      "page_number": null,
      "similarity_score": 0.767,
      "chunk_id": 4
    }
  ],
  "retrieval_time_ms": 15.2,
  "generation_time_ms": 1200.4,
  "total_time_ms": 1215.6,
  "model_name": "gemini-3.5-flash",
  "prompt_context_length": 4200,
  "chunk_count": 3
}
```

Render `data.answer`. For each source, render `filename`, `similarity_score` (for example, `toFixed(3)`), and only render `Page: ${page_number}` when `page_number !== null`. Page numbers are currently only available when supplied by the document chunk; `null` means no page reference is available.

```tsx
<p>{data.answer}</p>
{data.sources.map((source) => (
  <div key={`${source.document_id}-${source.chunk_id ?? source.filename}`}>
    <div>Source: {source.filename}</div>
    <div>Similarity: {source.similarity_score.toFixed(3)}</div>
    {source.page_number !== null && <div>Page: {source.page_number}</div>}
  </div>
))}
```

Optionally display `total_time_ms` as the response time; retrieval and generation timings are also available separately.

## Errors and loading states

All API errors have this safe structure:

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "The requested document has not been indexed."
  }
}
```

Handle them without exposing a raw backend response to users:

```ts
if (!response.ok) {
  const error = await response.json();
  setError(error.error?.message ?? "Please try again.");
  return;
}
```

| Status | Meaning | Suggested UI action |
| --- | --- | --- |
| 400 | Invalid PDF, file type, document ID, or request | Show the returned message and let the user correct the input. |
| 404 | The document ID is unknown or not indexed | Ask the user to upload/select a document again. |
| 409 | A supplied upload `document_id` already exists | Generate/select a different document ID, or omit it and let the API generate one. |
| 413 | PDF exceeds the configured upload limit | Ask for a smaller PDF. |
| 422 | Invalid or blank question/request body | Keep the form active and show validation feedback. |
| 500 | Indexing or unexpected server failure | Show a retry message. |
| 503 | RAG/Gemini answer service temporarily unavailable | Preserve the question and offer retry. |

Recommended UI states:

- Upload: `Uploading PDF...` -> `Indexing document...` -> `Document ready.`
- Question: `Searching course material...` -> `Generating answer...` -> `Answer ready.`

The upload endpoint completes after indexing, so switch to `Document ready.` only after its successful response. The question endpoint does not stream progress; use the two question loading labels as a single in-flight state unless the API later adds streaming/progress events.

## Current development limitation

The document registry is in memory, so uploaded-document records are lost when the FastAPI process restarts. The frontend should treat the returned `document_id` as valid for the current running backend and handle `404` by prompting for re-upload. Persistent document management will be integrated later behind the existing API boundary.
