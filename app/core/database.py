from contextlib import contextmanager
import psycopg2
from pgvector.psycopg2 import register_vector
from app.core.config import settings


@contextmanager
def get_connection(register_vector_type: bool = True):
    # Neon pooled endpoints reject PostgreSQL startup options such as statement_timeout.
    conn = psycopg2.connect(
        settings.database_url,
        connect_timeout=8,
        application_name="rag-demo-api",
    )
    try:
        if register_vector_type:
            register_vector(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    dimensions = int(settings.embedding_dimensions)
    if dimensions < 1 or dimensions > 16000:
        raise RuntimeError("EMBEDDING_DIMENSIONS must be between 1 and 16000")
    # On a new Neon database, the vector type does not exist until the extension is created.
    with get_connection(register_vector_type=False) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (tenant_id, slug)
                )
            """)
            cur.execute("""
                INSERT INTO knowledge_bases (tenant_id, slug, name)
                VALUES (%s, 'default', 'Default knowledge base')
                ON CONFLICT (tenant_id, slug) DO NOTHING
            """, (settings.tenant_id,))
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id UUID PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    knowledge_base_slug TEXT NOT NULL DEFAULT 'default',
                    filename TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id BIGSERIAL PRIMARY KEY,
                    document_id UUID NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    embedding VECTOR({dimensions}) NOT NULL,
                    tenant_id TEXT NOT NULL DEFAULT 'default',
                    knowledge_base_slug TEXT NOT NULL DEFAULT 'default',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (document_id, chunk_index)
                )
            """)
            cur.execute("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default'")
            cur.execute("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS knowledge_base_slug TEXT NOT NULL DEFAULT 'default'")
            cur.execute("CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx ON document_chunks (document_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS document_chunks_scope_idx ON document_chunks (tenant_id, knowledge_base_slug)")
            cur.execute("CREATE INDEX IF NOT EXISTS documents_scope_idx ON documents (tenant_id, knowledge_base_slug)")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx
                ON document_chunks USING hnsw (embedding vector_cosine_ops)
            """)
