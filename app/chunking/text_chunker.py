"""
Semantic text chunker for RAG applications.

The chunker preserves paragraph boundaries whenever possible and
uses sentence boundaries before falling back to character limits.
"""

import re

from app.models.document_chunk import DocumentChunk


class TextChunker:
    """Creates semantically meaningful overlapping chunks."""

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
    ):

        self.chunk_size = chunk_size
        self.overlap = overlap

    def _clean_text(self, text: str) -> str:
        """Normalize whitespace while preserving paragraphs."""

        # Normalize line endings
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        # Remove excessive spaces
        text = re.sub(r"[ \t]+", " ", text)

        # Preserve paragraph breaks
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _split_paragraphs(self, text: str) -> list[str]:
        """Split document into logical paragraphs."""

        paragraphs = []

        for para in text.split("\n\n"):

            para = para.strip()

            if para:
                paragraphs.append(para)

        return paragraphs

    def _split_large_paragraph(self, paragraph: str) -> list[str]:
        """
        Split a very large paragraph using sentence boundaries.
        """

        if len(paragraph) <= self.chunk_size:
            return [paragraph]

        # Split after punctuation
        sentences = re.split(
            r'(?<=[.!?])\s+',
            paragraph,
        )

        chunks = []
        current = ""

        for sentence in sentences:

            if len(current) + len(sentence) + 1 <= self.chunk_size:

                if current:
                    current += " "

                current += sentence

            else:

                if current:
                    chunks.append(current.strip())

                current = sentence

        if current:
            chunks.append(current.strip())

        return chunks

    def chunk_text(
        self,
        text: str,
        source_file: str,
    ) -> list[DocumentChunk]:
        """Generate overlapping semantic chunks wrapped in DocumentChunk objects.

        Args:
            text: The document text to chunk.
            source_file: Name or path of the source file.

        Returns:
            A list of DocumentChunk objects.
        """

        text = self._clean_text(text)

        paragraphs = self._split_paragraphs(text)

        processed = []

        # Handle oversized paragraphs first
        for para in paragraphs:

            processed.extend(
                self._split_large_paragraph(para)
            )

        chunks = []

        current = ""

        for para in processed:

            if len(current) + len(para) + 2 <= self.chunk_size:

                if current:
                    current += "\n\n"

                current += para

            else:

                if current:
                    chunks.append(current.strip())

                current = para

        if current:
            chunks.append(current.strip())

        # Add overlap
        final_chunks = []

        for i, chunk in enumerate(chunks):

            if i == 0:
                final_chunks.append(chunk)
                continue

            previous = final_chunks[-1]

            overlap_text = previous[-self.overlap:]

            # don't start in middle of word
            space = overlap_text.find(" ")

            if space != -1:
                overlap_text = overlap_text[space + 1:]

            final_chunks.append(
                overlap_text + "\n\n" + chunk
            )

        # Wrap chunks in DocumentChunk objects
        document_chunks = []
        for chunk_id, chunk_text in enumerate(final_chunks, start=1):
            doc_chunk = DocumentChunk(
                document_id=source_file,
                chunk_id=chunk_id,
                text=chunk_text,
                source_file=source_file,
            )
            document_chunks.append(doc_chunk)

        return document_chunks
