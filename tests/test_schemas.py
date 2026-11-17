import pytest
from pydantic import ValidationError
from app.schemas.documents import QueryRequest, KnowledgeBaseCreate, TextIngestRequest


def test_query_defaults_to_default_knowledge_base():
    request = QueryRequest(question="What is RAG?")
    assert request.knowledge_base == "default"


def test_query_rejects_invalid_knowledge_base_slug():
    with pytest.raises(ValidationError):
        QueryRequest(question="What is RAG?", knowledge_base="../other")


def test_knowledge_base_slug_validation():
    assert KnowledgeBaseCreate(slug="internal_docs", name="Internal docs").slug == "internal_docs"
    with pytest.raises(ValidationError):
        KnowledgeBaseCreate(slug="UPPER CASE", name="Invalid")


def test_text_ingestion_request_defaults_to_default_knowledge_base():
    request = TextIngestRequest(filename="notes.txt", text="hello")
    assert request.knowledge_base == "default"


def test_text_ingestion_rejects_invalid_knowledge_base_slug():
    with pytest.raises(ValidationError):
        TextIngestRequest(filename="notes.txt", text="hello", knowledge_base="../private")
