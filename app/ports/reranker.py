"""Contract for reranking an initial set of retrieved passages."""
from typing import Any, Protocol


class Reranker(Protocol):
    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Return the best candidate passages in relevance order."""
