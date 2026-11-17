"""Lightweight, local lexical reranker for retrieved candidate chunks."""
import re
from typing import Any

_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "how", "i", "in", "is", "it", "of", "on", "or", "that", "the",
    "this", "to", "was", "what", "when", "where", "which", "who", "why",
    "with",
}


def _terms(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]+", value.lower())
        if token not in _STOP_WORDS and len(token) > 1
    }


def rerank_chunks(
    question: str,
    chunks: list[dict[str, Any]],
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Reorder vector-search candidates using query-term coverage.

    This deterministic baseline is not a learned cross-encoder. Original
    vector distance is retained so a model-based reranker can replace it.
    """
    query_terms = _terms(question)
    if not query_terms:
        return chunks[:top_k] if top_k is not None else list(chunks)

    ranked = []
    for position, chunk in enumerate(chunks):
        content_terms = _terms(str(chunk.get("content", "")))
        lexical_score = len(query_terms & content_terms) / len(query_terms)
        distance = max(0.0, float(chunk.get("distance", 1.0)))
        vector_score = 1.0 / (1.0 + distance)
        rerank_score = (0.7 * lexical_score) + (0.3 * vector_score)
        enriched = dict(chunk)
        enriched["lexical_score"] = round(lexical_score, 6)
        enriched["rerank_score"] = round(rerank_score, 6)
        ranked.append((rerank_score, -position, enriched))

    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    results = [item[2] for item in ranked]
    return results[:top_k] if top_k is not None else results
