"""OpenAI client wrapper for the AI Academic Mentor application."""

import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from openai import OpenAIError
from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError

from .base_client import BaseLLMClient, LLMClientError

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """Client wrapper for OpenAI responses API."""

    def __init__(self) -> None:
        """Initialize the OpenAI client using environment variables."""
        project_root = Path(__file__).resolve().parents[2]
        dotenv_path = project_root / ".env"
        load_dotenv(dotenv_path=dotenv_path)
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMClientError(
                "Missing OPENAI_API_KEY environment variable."
            )

        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, prompt: str) -> str:
        """Generate text from OpenAI for the provided prompt."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt text must not be empty.")

        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                max_output_tokens=1024,
                temperature=0.2,
            )
            return self._extract_text(response)
        except AuthenticationError as exc:
            logger.exception("OpenAI authentication failed.")
            raise LLMClientError(
                "Authentication failed. Check your OPENAI_API_KEY."
            ) from exc
        except RateLimitError as exc:
            error_code = getattr(exc, "code", None)
            logger.exception("OpenAI rate limit or quota error: %s", error_code)
            if error_code == "insufficient_quota":
                raise LLMClientError(
                    "OpenAI API quota exceeded. Check your plan and billing details."
                ) from exc
            raise LLMClientError(
                "OpenAI rate limit exceeded. Please retry after a short delay."
            ) from exc
        except APIConnectionError as exc:
            logger.exception("OpenAI connection error.")
            raise LLMClientError(
                "Network error connecting to OpenAI. Check your connection."
            ) from exc
        except APITimeoutError as exc:
            logger.exception("OpenAI request timed out.")
            raise LLMClientError(
                "OpenAI request timed out. Please try again later."
            ) from exc
        except OpenAIError as exc:
            logger.exception("OpenAI API error.")
            raise LLMClientError(
                "An error occurred while communicating with OpenAI."
            ) from exc

    def _extract_text(self, response: Any) -> str:
        """Extract textual output from the OpenAI response object."""
        if response is None:
            raise LLMClientError("OpenAI returned an empty response.")

        if hasattr(response, "output_text") and response.output_text:
            return str(response.output_text).strip()

        if hasattr(response, "text") and response.text:
            return str(response.text).strip()

        output = getattr(response, "output", None)
        if isinstance(output, str) and output.strip():
            return output.strip()

        if isinstance(output, list):
            text_chunks = []
            for item in output:
                if isinstance(item, str) and item.strip():
                    text_chunks.append(item.strip())
                    continue

                if isinstance(item, dict):
                    if item.get("type") == "message":
                        content = item.get("content")
                        text_chunks.extend(self._extract_text_from_content(content))
                    elif "text" in item and isinstance(item["text"], str):
                        text_chunks.append(item["text"].strip())

            if text_chunks:
                return "\n".join(text_chunks).strip()

        raise LLMClientError("Unable to parse text from the OpenAI response.")

    def _extract_text_from_content(self, content: Any) -> list[str]:
        """Extract text values from nested response content structures."""
        if isinstance(content, str):
            return [content.strip()] if content.strip() else []

        if isinstance(content, list):
            values = []
            for fragment in content:
                if isinstance(fragment, str) and fragment.strip():
                    values.append(fragment.strip())
                elif isinstance(fragment, dict):
                    values.extend(self._extract_text_from_content(fragment.get("text") or fragment.get("content")))
            return values

        if isinstance(content, dict):
            if "text" in content and isinstance(content["text"], str):
                return [content["text"].strip()]
            if "content" in content:
                return self._extract_text_from_content(content["content"])

        return []
