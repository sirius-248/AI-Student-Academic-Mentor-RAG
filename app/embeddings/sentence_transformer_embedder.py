from __future__ import annotations

"""SentenceTransformer embedder implementation.

This class wraps the sentence-transformers library and exposes a minimal,
stable interface defined by BaseEmbedder. The underlying model is loaded once
and cached per model_name to avoid repeated initialization costs.
"""
from typing import List, Optional, Dict
import logging
import time
import threading

from .base_embedder import BaseEmbedder, EmbedderInitializationError

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder(BaseEmbedder):
    """Embedder using the sentence-transformers library.

    Args:
        model_name: The HuggingFace / sentence-transformers model identifier.
        device: Device string passed to SentenceTransformer (e.g. 'cpu', 'cuda', 'auto').
        batch_size: Preferred batch size when embedding large lists of texts.

    Notes:
        - The model is cached per model_name at the class level to avoid reloading.
        - If sentence-transformers is not installed an EmbedderInitializationError is raised.
    """

    # Class-level cache for loaded models to avoid reloading.
    _model_cache: Dict[str, object] = {}
    _cache_lock = threading.Lock()

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: str = "auto", batch_size: int = 64):
        self.model_name = model_name
        self.batch_size = int(batch_size) if batch_size and int(batch_size) > 0 else 64
        self.device = device
        self._model = self._load_model()

    def _detect_device(self) -> str:
        """Return a resolved device string for sentence-transformers.

        "auto" resolves to "cuda" if torch.cuda.is_available() else "cpu".
        """
        if isinstance(self.device, str) and self.device.lower() == "auto":
            try:
                import torch

                return "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                # If torch is not available, fall back to cpu
                return "cpu"
        return self.device

    def _load_model(self):
        """Load or reuse a SentenceTransformer model instance.

        Raises:
            EmbedderInitializationError: if sentence-transformers cannot be imported
                or the model fails to load.
        """
        # Return cached model when available
        with self._cache_lock:
            if self.model_name in self._model_cache:
                logger.info("Using cached SentenceTransformer model '%s'", self.model_name)
                return self._model_cache[self.model_name]

            # Lazy import to avoid hard dependency until this embedder is used
            try:
                from sentence_transformers import SentenceTransformer
            except Exception as exc:
                logger.error("sentence-transformers is required for SentenceTransformerEmbedder: %s", exc)
                raise EmbedderInitializationError(
                    "sentence-transformers is not installed. Install with 'pip install sentence-transformers'"
                ) from exc

            resolved_device = self._detect_device()
            logger.info("Loading SentenceTransformer model '%s' on device '%s'", self.model_name, resolved_device)
            try:
                model = SentenceTransformer(self.model_name, device=resolved_device)
            except Exception as exc:
                logger.exception("Failed to load SentenceTransformer model '%s'", self.model_name)
                raise EmbedderInitializationError(f"Failed to load model {self.model_name}: {exc}") from exc

            self._model_cache[self.model_name] = model
            return model

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string and return a vector as a list of floats.

        This method delegates to embed_batch to ensure consistency.
        """
        if text is None:
            logger.warning("Received None in embed_text; converting to empty string")
            text = ""
        if not isinstance(text, str):
            # Be permissive and convert to str but log
            logger.warning("embed_text received non-str input of type %s; converting with str()", type(text))
            text = str(text)

        embeddings = self.embed_batch([text])
        return embeddings[0]

    def embed_batch(self, texts: List[Optional[str]]) -> List[List[float]]:
        """Embed a batch of texts.

        Args:
            texts: List of strings (or None). None entries are converted to empty strings
                   to preserve positional alignment.

        Returns:
            List of embedding vectors (each a list of floats) in the same order as inputs.
        """
        if texts is None:
            raise ValueError("texts must be an iterable of strings (got None)")

        # Ensure we operate on a list to allow indexing/slicing
        input_texts = list(texts)
        n = len(input_texts)
        logger.info("Embedding batch of %d items using model '%s' (batch_size=%d)", n, self.model_name, self.batch_size)

        # Normalize inputs: convert None to empty string and non-str via str()
        normalized: List[str] = []
        for i, t in enumerate(input_texts):
            if t is None:
                logger.debug("Item %d is None; converting to empty string", i)
                normalized.append("")
            elif not isinstance(t, str):
                logger.debug("Item %d is type %s; converting via str()", i, type(t))
                normalized.append(str(t))
            else:
                normalized.append(t)

        model = self._model
        results: List[List[float]] = []

        start_time = time.time()

        # Use model.encode with built-in batching when possible
        try:
            # sentence-transformers accepts batch_size argument and returns numpy array if convert_to_numpy=True
            # We will call encode over slices to explicitly control memory and progress logging.
            batch_size = max(1, int(self.batch_size))
            for i in range(0, n, batch_size):
                batch_texts = normalized[i : i + batch_size]
                logger.debug("Encoding batch %d - %d", i, min(i + batch_size, n))
                embeddings = model.encode(batch_texts, batch_size=len(batch_texts), convert_to_numpy=True, show_progress_bar=False)
                # Convert numpy arrays to python lists of floats
                for vec in embeddings:
                    results.append([float(x) for x in vec.tolist()])
                logger.debug("Completed batch: %d - %d", i, min(i + batch_size, n))
        except Exception as exc:
            logger.exception("Error during embedding: %s", exc)
            raise EmbedderInitializationError(f"Error during embedding: {exc}") from exc

        elapsed = time.time() - start_time
        logger.info("Completed embedding %d items in %.3fs", n, elapsed)
        return results
