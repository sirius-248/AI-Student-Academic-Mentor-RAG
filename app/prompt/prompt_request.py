"""Data model for prompt generation requests.

Encapsulates the user question, retrieved search context, optional conversation history,
and customizable system instructions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from app.retriever.retrieved_context import RetrievedContext


@dataclass
class PromptRequest:
    """Represents a request to generate an LLM prompt.

    Attributes:
        question: The user query string.
        retrieved_context: RetrievedContext object containing matched search results.
        conversation_history: Optional list of past conversation turns for multi-turn RAG.
        system_instructions: Optional custom system prompt override.
        language: Optional target response language.
    """

    question: str
    retrieved_context: RetrievedContext
    conversation_history: Optional[List[Dict[str, str]]] = None
    system_instructions: Optional[str] = None
    language: Optional[str] = None
