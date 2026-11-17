"""Small offline retrieval metrics for evaluating RAG search quality."""
from collections.abc import Iterable, Sequence


def precision_at_k(retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    if k <= 0:
        return 0.0
    relevant = set(relevant_ids)
    selected = list(retrieved_ids[:k])
    if not selected:
        return 0.0
    return sum(item in relevant for item in selected) / len(selected)


def recall_at_k(retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    relevant = set(relevant_ids)
    if k <= 0 or not relevant:
        return 0.0
    return len(set(retrieved_ids[:k]) & relevant) / len(relevant)


def reciprocal_rank(retrieved_ids: Sequence[str], relevant_ids: Iterable[str]) -> float:
    relevant = set(relevant_ids)
    for rank, item in enumerate(retrieved_ids, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(
    rankings: Sequence[tuple[Sequence[str], Iterable[str]]],
) -> float:
    if not rankings:
        return 0.0
    return sum(reciprocal_rank(retrieved, relevant) for retrieved, relevant in rankings) / len(rankings)


def evaluate_retrieval(
    retrieved_ids: Sequence[str],
    relevant_ids: Iterable[str],
    k: int,
) -> dict[str, float]:
    relevant = set(relevant_ids)
    return {
        "precision_at_k": precision_at_k(retrieved_ids, relevant, k),
        "recall_at_k": recall_at_k(retrieved_ids, relevant, k),
        "reciprocal_rank": reciprocal_rank(retrieved_ids, relevant),
        "hit_rate": float(bool(set(retrieved_ids[:max(k, 0)]) & relevant)),
    }
