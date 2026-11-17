"""Contract for any service that converts text into embedding vectors."""
from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one vector for each input text, preserving input order."""
