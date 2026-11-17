import json
import pytest
from app.services.extractor import extract_text


def test_extract_plain_text():
    assert extract_text("notes.txt", b"Hello RAG") == "Hello RAG"


def test_extract_markdown():
    assert "## RAG" in extract_text("notes.md", b"## RAG")


def test_extract_json_pretty_prints():
    result = extract_text("data.json", b'{"answer":42}')
    assert '"answer": 42' in result


def test_reject_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text("secret.exe", b"no")


def test_reject_empty_text():
    with pytest.raises(ValueError, match="No extractable text"):
        extract_text("empty.txt", b"  ")
