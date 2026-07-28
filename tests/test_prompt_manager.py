from app.prompts.prompts import PromptManager


def test_create_summary_prompt_includes_instructions() -> None:
    document_text = "Sample syllabus content."
    prompt = PromptManager.create_summary_prompt(document_text)

    assert "You are an educational AI assistant" in prompt
    assert "Generate:" in prompt
    assert "One multiple choice question" in prompt
    assert "Sample syllabus content." in prompt
