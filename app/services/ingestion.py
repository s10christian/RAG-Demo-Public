"""Coordinates extraction, chunking, embedding, and persistence."""
from hashlib import sha256
from uuid import uuid4

from app.services.chunker import split_text
from app.services.embedder import Embedder
from app.services.extractor import extract_text
from app.services.vector_store import PgVectorStore


def ingest_document(filename: str, content: bytes, knowledge_base_slug: str = "default", document_id: str | None = None) -> tuple[str, int]:
    digest = sha256(content).hexdigest()
    document_id = document_id or str(uuid4())
    store = PgVectorStore()
    text = extract_text(filename, content)
    chunks = split_text(text)
    if not chunks:
        raise ValueError("Document produced no usable text chunks")
    vectors = Embedder().embed(chunks)
    store.add_document(document_id=document_id, filename=filename, content_hash=digest, chunks=chunks, embeddings=vectors, knowledge_base_slug=knowledge_base_slug)
    return document_id, len(chunks)
