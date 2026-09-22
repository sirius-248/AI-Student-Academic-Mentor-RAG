"""Infrastructure-independent RAG application service."""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Iterable, Protocol, Sequence

from .answer_response import AnswerResponse
from .config import PipelineConfig
from .document_metadata import DocumentMetadata
from .exceptions import (
    PipelineConfigurationError,
    PipelineGenerationError,
    PipelineIndexingError,
    PipelineValidationError,
)
from .indexing_result import IndexingResult
from .source_reference import SourceReference

logger = logging.getLogger(__name__)


class _Reader(Protocol):
    def extract_text(self, file_path: str | None = None) -> str: ...


class _Preprocessor(Protocol):
    def execute(self, text: str) -> str: ...


class _Chunker(Protocol):
    def chunk_text(self, text: str, source_file: str) -> Sequence[Any]: ...


class _EmbeddingService(Protocol):
    def embed_chunks(self, chunks: Sequence[Any]) -> Sequence[Any]: ...


class _VectorStore(Protocol):
    def add_documents(self, chunks: Sequence[Any]) -> None: ...

    def save(self) -> None: ...


class _Retriever(Protocol):
    def retrieve_context(self, query: str, top_k: int | None = None, document_ids: Sequence[str] | None = None) -> Any: ...


class _PromptBuilder(Protocol):
    def build_prompt(self, request: Any) -> Any: ...


class _GeminiClient(Protocol):
    def generate(self, prompt: str) -> str: ...


class RAGPipeline:
    """Coordinates injected RAG services through indexing and answer operations only."""

    def __init__(
        self,
        *,
        reader: _Reader | None = None,
        preprocessing: _Preprocessor | None = None,
        chunker: _Chunker | None = None,
        embedding_service: _EmbeddingService | None = None,
        vector_store: _VectorStore | None = None,
        retriever: _Retriever | None = None,
        prompt_builder: _PromptBuilder | None = None,
        gemini_client: _GeminiClient | None = None,
        config: PipelineConfig | None = None,
    ) -> None:
        """Create a pipeline with injected services or the production defaults.

        Explicit dependencies remain supported for tests and alternate runtime
        composition.  When omitted, the default application services are
        constructed here so entry points only depend on this facade.
        """
        if reader is None:
            from app.document_reader.pdf_reader import PDFReader
            reader = PDFReader()
        if preprocessing is None:
            from app.preprocessing.pipeline import PreprocessingPipeline
            preprocessing = PreprocessingPipeline()
        if chunker is None:
            from app.chunking.text_chunker import TextChunker
            chunker = TextChunker()
        if embedding_service is None:
            from app.embeddings.embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
        if vector_store is None:
            from app.vector_store.vector_store_factory import VectorStoreFactory
            vector_store = VectorStoreFactory.get_vector_store()
        if retriever is None:
            from app.retriever.retriever import Retriever
            retriever = Retriever(embedding_service=embedding_service, vector_store=vector_store)
        if prompt_builder is None:
            from app.prompt.prompt_builder import PromptBuilder
            prompt_builder = PromptBuilder()
        if gemini_client is None:
            from app.llm.gemini_client import GeminiClient
            gemini_client = GeminiClient()
        dependencies = {
            "reader": reader, "preprocessing": preprocessing, "chunker": chunker,
            "embedding_service": embedding_service, "vector_store": vector_store,
            "retriever": retriever, "prompt_builder": prompt_builder,
            "gemini_client": gemini_client,
        }
        missing = [name for name, dependency in dependencies.items() if dependency is None]
        if missing:
            raise PipelineConfigurationError("Missing required dependencies: " + ", ".join(missing))
        self._reader = reader
        self._preprocessing = preprocessing
        self._chunker = chunker
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._retriever = retriever
        self._prompt_builder = prompt_builder
        self._gemini_client = gemini_client
        self._config = config or PipelineConfig.from_environment()

    def index_document(self, document_path: str | Path, document_id: str | None = None) -> IndexingResult:
        """Read, clean, chunk, embed, and persist one document."""
        path = self._validated_document_path(document_path)
        normalized_id = self._validated_document_id(document_id, path)
        started = time.perf_counter()
        logger.info("Indexing document", extra={"document_id": normalized_id, "source_filename": path.name})
        try:
            raw_text = self._reader.extract_text(str(path))
            clean_text = self._preprocessing.execute(raw_text)
            if not isinstance(clean_text, str) or not clean_text.strip():
                raise ValueError("preprocessing produced no indexable text")
            chunks = list(self._chunker.chunk_text(clean_text, path.name))
            if not chunks:
                raise ValueError("chunker produced no chunks")
            for chunk in chunks:
                setattr(chunk, "document_id", normalized_id)
                if not getattr(chunk, "source_file", None):
                    setattr(chunk, "source_file", path.name)
            embedded_chunks = list(self._embedding_service.embed_chunks(chunks))
            if len(embedded_chunks) != len(chunks):
                raise ValueError("embedding service returned a different number of chunks")
            self._vector_store.add_documents(embedded_chunks)
            if self._config.auto_save_index:
                self._vector_store.save()
            metadata = DocumentMetadata.from_path(path, normalized_id, self._page_count())
            elapsed = (time.perf_counter() - started) * 1000
            logger.info("Document indexed", extra={"document_id": normalized_id, "chunks": len(chunks), "duration_ms": round(elapsed, 2)})
            return IndexingResult(metadata, len(chunks), len(embedded_chunks), elapsed)
        except PipelineValidationError:
            raise
        except Exception as exc:
            logger.exception("Document indexing failed", extra={"document_id": normalized_id, "source_filename": path.name})
            raise PipelineIndexingError(f"Unable to index document '{path.name}'") from exc

    def answer_question(
        self, question: str, *, top_k: int | None = None, document_ids: Sequence[str] | None = None
    ) -> AnswerResponse:
        """Retrieve evidence, build a RAG prompt, and generate an answer."""
        query = self._validated_question(question)
        effective_top_k = top_k if top_k is not None else self._config.default_top_k
        if effective_top_k is not None and (
            not isinstance(effective_top_k, int)
            or isinstance(effective_top_k, bool)
            or effective_top_k < 1
        ):
            raise PipelineValidationError("top_k must be a positive integer")
        allowed_ids = self._validated_document_ids(document_ids)
        started = time.perf_counter()
        logger.info("Answering question", extra={"question_length": len(query), "top_k": effective_top_k})
        try:
            context = self._retriever.retrieve_context(
                query,
                top_k=effective_top_k,
                document_ids=allowed_ids,
            )
            results = tuple(getattr(context, "results", ()))
            if allowed_ids is not None:
                results = tuple(result for result in results if getattr(getattr(result, "chunk", None), "document_id", None) in allowed_ids)
                context = self._context_with_results(context, results)
            prompt = self._prompt_builder.build_prompt(self._prompt_request(query, context))
            generation_started = time.perf_counter()
            answer = self._gemini_client.generate(prompt.full_prompt)
            generation_ms = (time.perf_counter() - generation_started) * 1000
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("Gemini client returned an empty answer")
            total_ms = (time.perf_counter() - started) * 1000
            return AnswerResponse(
                answer=answer.strip(), sources=self._source_references(results),
                retrieval_time_ms=float(getattr(context, "retrieval_time_ms", 0.0)),
                generation_time_ms=generation_ms, total_time_ms=total_ms,
                prompt_context_length=int(getattr(prompt, "context_length", 0)),
                chunk_count=int(getattr(prompt, "chunk_count", len(results))),
                model_name=getattr(self._gemini_client, "model", None),
            )
        except PipelineValidationError:
            raise
        except Exception as exc:
            logger.exception("Question answering failed", extra={"question_length": len(query)})
            raise PipelineGenerationError("Unable to answer the question") from exc

    def _validated_document_path(self, value: str | Path) -> Path:
        if not isinstance(value, (str, Path)) or not str(value).strip():
            raise PipelineValidationError("document_path must be a non-empty path")
        path = Path(value)
        if not path.is_file():
            raise PipelineValidationError(f"Document does not exist: {path}")
        return path

    @staticmethod
    def _validated_document_id(value: str | None, path: Path) -> str:
        if value is None:
            return path.stem
        if not isinstance(value, str) or not value.strip():
            raise PipelineValidationError("document_id must be a non-empty string when supplied")
        return value.strip()

    @staticmethod
    def _validated_question(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise PipelineValidationError("question must be a non-empty string")
        return value.strip()

    @staticmethod
    def _validated_document_ids(value: Sequence[str] | None) -> frozenset[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            raise PipelineValidationError("document_ids must be a sequence of document IDs, not a string")
        ids = frozenset(item.strip() for item in value if isinstance(item, str) and item.strip())
        if not ids:
            raise PipelineValidationError("document_ids must contain at least one non-empty ID")
        return ids

    def _page_count(self) -> int | None:
        extract_pages = getattr(self._reader, "extract_pages", None)
        if not callable(extract_pages):
            return None
        try:
            return len(extract_pages())
        except Exception:
            logger.debug("Reader does not provide page count for this document", exc_info=True)
            return None

    @staticmethod
    def _context_with_results(context: Any, results: tuple[Any, ...]) -> Any:
        from dataclasses import replace
        try:
            return replace(context, results=list(results))
        except (TypeError, ValueError):
            from types import SimpleNamespace
            return SimpleNamespace(query=getattr(context, "query", ""), results=list(results), retrieval_time_ms=getattr(context, "retrieval_time_ms", 0.0), top_k=getattr(context, "top_k", len(results)))

    @staticmethod
    def _prompt_request(question: str, context: Any) -> Any:
        # PromptBuilder consumes this small request contract.  Keeping it local
        # prevents the orchestration layer from being coupled to a particular
        # prompt-request implementation.
        from types import SimpleNamespace
        return SimpleNamespace(
            question=question,
            retrieved_context=context,
            conversation_history=None,
            system_instructions=None,
            language=None,
        )

    @staticmethod
    def _source_references(results: Iterable[Any]) -> tuple[SourceReference, ...]:
        references: list[SourceReference] = []
        seen: set[tuple[Any, ...]] = set()
        for result in results:
            chunk = getattr(result, "chunk", None)
            if chunk is None:
                continue
            reference = SourceReference(str(getattr(chunk, "document_id", "unknown")), str(getattr(chunk, "source_file", "unknown")), getattr(chunk, "page_number", None), float(getattr(result, "score", 0.0)), getattr(chunk, "chunk_id", None))
            key = (reference.document_id, reference.filename, reference.page_number, reference.chunk_id)
            if key not in seen:
                seen.add(key)
                references.append(reference)
        return tuple(references)
