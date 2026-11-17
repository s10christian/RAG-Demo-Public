"""Contract for storing documents and searching embedded chunks."""
from typing import Any, Protocol


class VectorStore(Protocol):
    def add_document(
        self,
        document_id: str,
        filename: str,
        content_hash: str,
        chunks: list[str],
        embeddings: list[list[float]],
        knowledge_base_slug: str,
    ) -> None:
        """Persist a document and all of its embedded chunks."""

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        knowledge_base_slug: str = "default",
    ) -> list[dict[str, Any]]:
        """Return the nearest chunks, best match first."""
