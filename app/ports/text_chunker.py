"""Contract for splitting extracted text into searchable passages."""
from typing import Protocol


class TextChunker(Protocol):
    def split_text(self, text: str) -> list[str]:
        """Return a list of non-empty text chunks."""
