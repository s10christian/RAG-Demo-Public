import pytest

from app.services.prompt_builder import build_rag_messages


def test_prompt_builder_includes_question_and_source():
    messages = build_rag_messages(
        "What is RAG?",
        [{"source_name": "guide.md", "chunk_index": 2, "content": "RAG retrieves context."}],
    )
    assert messages[0]["role"] == "system"
    assert "reference data" in messages[0]["content"]
    assert "What is RAG?" in messages[1]["content"]
    assert "[Source 1] File: guide.md | Chunk: 2" in messages[1]["content"]


def test_prompt_builder_rejects_blank_question():
    with pytest.raises(ValueError, match="must not be empty"):
        build_rag_messages("  ", [])
