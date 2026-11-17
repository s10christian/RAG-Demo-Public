from app.services import retriever


def test_retriever_embeds_query_and_returns_matching_vector_store_chunks(monkeypatch):
    observed = {}

    class FakeEmbedder:
        def embed(self, texts):
            observed["texts"] = texts
            return [[0.1, 0.2, 0.3]]

    class FakeVectorStore:
        def search(self, query_vector, top_k, knowledge_base_slug):
            observed["search"] = (query_vector, top_k, knowledge_base_slug)
            return [{
                "document_id": "notion-document-1",
                "source_name": "notion-project-roadmap.md",
                "content": "Deployment status: production rollout is complete.",
                "distance": 0.08,
            }]

    monkeypatch.setattr(retriever, "Embedder", FakeEmbedder)
    monkeypatch.setattr(retriever, "PgVectorStore", FakeVectorStore)

    results = retriever.retrieve(
        "What is the production rollout status?",
        top_k=3,
        knowledge_base_slug="default",
    )

    assert observed["texts"] == ["What is the production rollout status?"]
    assert observed["search"] == ([0.1, 0.2, 0.3], 3, "default")
    assert len(results) == 1
    assert results[0]["document_id"] == "notion-document-1"
    assert "production rollout is complete" in results[0]["content"]
