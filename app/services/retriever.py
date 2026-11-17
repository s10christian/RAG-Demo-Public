"""Embeds a query and retrieves the closest chunks from the vector store."""
from app.services.embedder import Embedder
from app.services.vector_store import PgVectorStore


def retrieve(
    question: str,
    top_k: int,
    knowledge_base_slug: str = "default",
) -> list[dict]:
    vector = Embedder().embed([question])[0]
    return PgVectorStore().search(vector, top_k, knowledge_base_slug)
