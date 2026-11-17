CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_bases (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, slug)
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    knowledge_base_slug TEXT NOT NULL DEFAULT 'default',
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    source_name TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding VECTOR(1536) NOT NULL,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    knowledge_base_slug TEXT NOT NULL DEFAULT 'default',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, chunk_index)
);

ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS knowledge_base_slug TEXT NOT NULL DEFAULT 'default';

CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx ON document_chunks (document_id);
CREATE INDEX IF NOT EXISTS document_chunks_scope_idx ON document_chunks (tenant_id, knowledge_base_slug);
CREATE INDEX IF NOT EXISTS documents_scope_idx ON documents (tenant_id, knowledge_base_slug);
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx
    ON document_chunks USING hnsw (embedding vector_cosine_ops);
