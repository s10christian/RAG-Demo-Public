"""PostgreSQL/pgvector adapter for durable document and vector storage."""
from psycopg2.extras import Json
from app.core.config import settings
from app.core.database import get_connection


class PgVectorStore:
    def has_document(self, document_id: str, content_hash: str) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM documents WHERE id = %s AND tenant_id = %s AND sha256 = %s", (document_id, settings.tenant_id, content_hash))
                return cur.fetchone() is not None

    def add_document(self, document_id: str, filename: str, content_hash: str, chunks: list[str], embeddings: list[list[float]], knowledge_base_slug: str = "default") -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Every chunk must have exactly one embedding")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM knowledge_bases WHERE tenant_id = %s AND slug = %s", (settings.tenant_id, knowledge_base_slug))
                if cur.fetchone() is None:
                    raise ValueError("Knowledge base does not exist")
                cur.execute("DELETE FROM document_chunks WHERE document_id = %s AND tenant_id = %s", (document_id, settings.tenant_id))
                cur.execute("DELETE FROM documents WHERE id = %s AND tenant_id = %s", (document_id, settings.tenant_id))
                cur.execute("INSERT INTO documents (id, tenant_id, knowledge_base_slug, filename, sha256, chunk_count) VALUES (%s, %s, %s, %s, %s, %s)", (document_id, settings.tenant_id, knowledge_base_slug, filename, content_hash, len(chunks)))
                cur.executemany("INSERT INTO document_chunks (document_id, chunk_index, content, source_name, metadata, embedding, tenant_id, knowledge_base_slug) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", [(document_id, i, chunk, filename, Json({"origin": "notion" if filename.startswith("notion-") else "upload", "sha256": content_hash}), vector, settings.tenant_id, knowledge_base_slug) for i, (chunk, vector) in enumerate(zip(chunks, embeddings))])

    def search(self, query_vector: list[float], top_k: int, knowledge_base_slug: str = "default") -> list[dict]:
        limit = min(max(1, top_k), settings.max_top_k)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, document_id, content, source_name, chunk_index, (embedding <=> %s::vector) AS distance FROM document_chunks WHERE tenant_id = %s AND knowledge_base_slug = %s ORDER BY embedding <=> %s::vector LIMIT %s", (query_vector, settings.tenant_id, knowledge_base_slug, query_vector, limit))
                rows = cur.fetchall()
        return [{"chunk_id": r[0], "document_id": r[1], "content": r[2], "source_name": r[3], "chunk_index": r[4], "distance": float(r[5])} for r in rows]
