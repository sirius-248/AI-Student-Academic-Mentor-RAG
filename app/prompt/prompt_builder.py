"""Prompt builder orchestration layer.

Formats retrieved DocumentChunks into structured context blocks and populates
modular prompt templates for LLM generation.
"""
from __future__ import annotations

import logging
from typing import Optional, List

from app.vector_store.search_result import SearchResult

from .prompt_request import PromptRequest
from .prompt import Prompt
from .prompt_templates import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    RAG_PROMPT_TEMPLATE,
)
from .config import MAX_PROMPT_CONTEXT_LENGTH
from .exceptions import PromptValidationError, PromptBuilderError

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builder service for constructing structured LLM prompts from retrieval results."""

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        max_context_length: Optional[int] = None,
    ) -> None:
        """Initialize PromptBuilder.

        Args:
            system_prompt: Optional custom system prompt override. Defaults to SYSTEM_PROMPT.
            max_context_length: Optional maximum context character length. Defaults to config MAX_PROMPT_CONTEXT_LENGTH.
        """
        self.system_prompt = system_prompt or SYSTEM_PROMPT
        self.max_context_length = max_context_length or MAX_PROMPT_CONTEXT_LENGTH
        logger.info("Initialized PromptBuilder with max_context_length=%d", self.max_context_length)

    def _format_context_blocks(self, results: List[SearchResult]) -> str:
        """Format SearchResult objects into structured text context blocks.

        Args:
            results: List of SearchResult objects from retrieval.

        Returns:
            Formatted context string.
        """
        if not results:
            logger.warning("No retrieved search results provided for context formatting")
            return "No relevant context was found in the indexed documents."

        blocks: List[str] = []
        divider = "=" * 50

        for idx, result in enumerate(results):
            chunk = getattr(result, "chunk", None)
            if chunk is None:
                continue

            source = getattr(chunk, "source_file", "Unknown")
            page = getattr(chunk, "page_number", None)
            page_str = str(page) if page is not None else "N/A"
            text = getattr(chunk, "text", "")

            block = (
                f"{divider}\n"
                f"Source:\n{source}\n\n"
                f"Page:\n{page_str}\n\n"
                f"Content:\n{text}"
            )
            blocks.append(block)

        if not blocks:
            return "No relevant context was found in the indexed documents."

        combined = ("\n" + divider + "\n").join(blocks) + "\n" + divider
        return combined

    def build_prompt(self, request: PromptRequest) -> Prompt:
        """Build a complete Prompt object from a PromptRequest.

        Args:
            request: PromptRequest containing question, retrieved_context, and optional parameters.

        Returns:
            Prompt object containing system_prompt, user_prompt, full_prompt, and metrics.

        Raises:
            PromptValidationError: If request is invalid, missing question, or missing retrieved_context.
            PromptBuilderError: If template formatting fails.
        """
        if request is None:
            raise PromptValidationError("request cannot be None")
        if not hasattr(request, "question") or not request.question or not request.question.strip():
            raise PromptValidationError("request.question must be a non-empty string")
        if not hasattr(request, "retrieved_context") or request.retrieved_context is None:
            raise PromptValidationError("request.retrieved_context cannot be None")

        question = request.question.strip()
        results = getattr(request.retrieved_context, "results", [])
        chunk_count = len(results)

        logger.info("Starting prompt generation for question: '%s' (%d chunks)", question, chunk_count)

        # Step 1: Format context blocks
        formatted_context = self._format_context_blocks(results)
        context_len = len(formatted_context)

        # Step 2: Audit and handle context length
        if context_len > self.max_context_length:
            logger.warning(
                "Formatted context length (%d chars) exceeds max allowed (%d chars); truncating context",
                context_len,
                self.max_context_length,
            )
            formatted_context = formatted_context[: self.max_context_length] + "\n...[Context truncated]"
            context_len = len(formatted_context)

        logger.debug("Formatted context block: %d characters from %d chunks", context_len, chunk_count)

        # Step 3: Determine system prompt
        active_system_prompt = (
            request.system_instructions
            if request.system_instructions and request.system_instructions.strip()
            else self.system_prompt
        )

        # Step 4: Include conversation history if present
        user_content = USER_PROMPT_TEMPLATE.format(context=formatted_context, question=question)

        if request.conversation_history:
            history_blocks: List[str] = []
            for turn in request.conversation_history:
                user_msg = turn.get("user", "")
                assistant_msg = turn.get("assistant", "")
                if user_msg or assistant_msg:
                    history_blocks.append(f"User: {user_msg}\nAssistant: {assistant_msg}")

            if history_blocks:
                history_text = "\n---\n".join(history_blocks)
                user_content = f"Conversation History:\n{history_text}\n\n{user_content}"
                logger.debug("Included %d conversation history turns in user prompt", len(history_blocks))

        # Step 5: Compose full RAG prompt
        try:
            full_prompt_str = RAG_PROMPT_TEMPLATE.format(
                system_prompt=active_system_prompt,
                user_prompt=user_content,
            )
        except Exception as exc:
            logger.exception("Failed to format RAG prompt template: %s", exc)
            raise PromptBuilderError(f"Prompt template formatting failed: {exc}") from exc

        logger.info("Successfully generated prompt (total length: %d chars)", len(full_prompt_str))

        return Prompt(
            system_prompt=active_system_prompt,
            user_prompt=user_content,
            full_prompt=full_prompt_str,
            context_length=context_len,
            chunk_count=chunk_count,
        )
