from app.services.reranker import rerank_chunks


def test_reranker_promotes_keyword_relevant_chunk():
    chunks = [
        {"content": "A general introduction to software.", "distance": 0.1},
        {"content": "Docker container networking and Docker bridge networks.", "distance": 0.8},
    ]
    result = rerank_chunks("Explain Docker networking", chunks, top_k=1)
    assert "Docker" in result[0]["content"]
    assert 0.0 <= result[0]["lexical_score"] <= 1.0
    assert "rerank_score" in result[0]


def test_reranker_preserves_order_for_empty_query_terms():
    chunks = [{"content": "first"}, {"content": "second"}]
    assert rerank_chunks("the and of", chunks) == chunks


def test_reranker_can_return_all_candidates():
    chunks = [{"content": "alpha"}, {"content": "beta"}]
    assert len(rerank_chunks("alpha", chunks)) == 2
