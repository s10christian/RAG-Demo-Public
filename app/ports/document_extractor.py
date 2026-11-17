"""Contract for converting an uploaded file into plain text."""
from typing import Protocol


class DocumentExtractor(Protocol):
    def extract_text(self, filename: str, content: bytes) -> str:
        """Return readable text extracted from the supplied file bytes."""
