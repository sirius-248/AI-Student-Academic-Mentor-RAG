"""Prompt templates for the AI Academic Mentor."""


class PromptManager:
    """Manage prompt generation for academic content."""

    @staticmethod
    def create_summary_prompt(document_text: str) -> str:
        """Build a syllabus summary prompt for the language model.

        Args:
            document_text: Syllabus text extracted from a PDF.

        Returns:
            A formatted prompt string for OpenAI.
        """
        return (
            "You are an educational AI assistant.\n\n"
            "Read the following syllabus.\n\n"
            "Generate:\n"
            "1. A concise summary.\n"
            "2. One multiple choice question.\n\n"
            "The MCQ should contain:\n"
            "Question\n"
            "Option A\n"
            "Option B\n"
            "Option C\n"
            "Option D\n"
            "Correct Answer\n"
            "Explanation\n\n"
            "Return plain text only.\n\n"
            "Syllabus:\n"
            f"{document_text.strip()}"
        )
