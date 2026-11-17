"""Coordinates retrieval, optional reranking, and grounded answer generation."""
from app.core.config import settings
from app.services.generator import generate_answer
from app.services.reranker import rerank_chunks
from app.services.retriever import retrieve


def answer_question(
    question: str,
    top_k: int,
    knowledge_base_slug: str = "default",
) -> tuple[str, list[dict]]:
    requested_k = min(max(1, top_k), settings.max_top_k)
    candidate_k = requested_k
    if settings.reranker_enabled:
        multiplier = max(1, settings.reranker_candidate_multiplier)
        candidate_k = min(requested_k * multiplier, settings.max_top_k)

    chunks = retrieve(question, candidate_k, knowledge_base_slug)
    if settings.reranker_enabled:
        chunks = rerank_chunks(question, chunks, requested_k)

    answer = generate_answer(question, chunks)
    return answer, chunks
