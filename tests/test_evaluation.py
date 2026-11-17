from app.services.evaluation import (
    evaluate_retrieval,
    mean_reciprocal_rank,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_precision_and_recall_at_k():
    retrieved = ["a", "x", "b"]
    relevant = {"a", "b"}
    assert precision_at_k(retrieved, relevant, 2) == 0.5
    assert recall_at_k(retrieved, relevant, 2) == 0.5


def test_reciprocal_rank_and_mrr():
    assert reciprocal_rank(["x", "b"], {"b"}) == 0.5
    assert mean_reciprocal_rank([
        (["a", "b"], {"b"}),
        (["x", "c"], {"c"}),
    ]) == 0.5


def test_empty_evaluation_is_safe():
    assert precision_at_k([], {"a"}, 5) == 0.0
    assert recall_at_k(["a"], set(), 5) == 0.0
    assert mean_reciprocal_rank([]) == 0.0
    assert evaluate_retrieval(["x"], {"a"}, 3)["hit_rate"] == 0.0
