# RAG pipeline modules

This repository is a modular monolith: one deployable API with independently understandable RAG stages.

## Ingestion path

1. **API boundary** — validates upload size, filename, knowledge-base scope, and request shape.
2. **Extractor** (app/services/extractor.py) — converts PDF, TXT, Markdown, DOCX, CSV, JSON, and HTML bytes into text.
3. **Chunker** (app/services/chunker.py) — splits text into overlapping passages.
4. **Embedder** (app/services/embedder.py) — converts each passage into a vector through an OpenAI-compatible embeddings endpoint.
5. **Vector store** — persists document metadata, chunks, and vectors in PostgreSQL/pgvector.
6. **Ingestion coordinator** (app/services/ingestion.py) — runs the stages in order and returns the document ID and chunk count.

## Query path

1. **Query API** validates the question and retrieval settings.
2. **Retriever** (app/services/retriever.py) embeds the question and performs scoped vector similarity search.
3. **Optional reranker** (app/services/reranker.py) reorders candidates using a lightweight local lexical relevance score. It is disabled by default; set RERANKER_ENABLED=true to enable it.
4. **Prompt builder** (app/services/prompt_builder.py) constructs the system and user messages and marks retrieved document text as reference data.
5. **Generator** (app/services/generator.py) calls the configured OpenAI-compatible chat-completions endpoint and returns a grounded answer.
6. **RAG coordinator** (app/services/rag.py) orchestrates retrieval, optional reranking, and generation.

## Supporting modules

- **Ports** (app/ports/) define replaceable contracts for extractors, chunkers, embedding providers, vector stores, and rerankers.
- **Schemas** (app/schemas/) define validated API inputs and outputs.
- **Evaluation** (app/services/evaluation.py) provides offline Precision@K, Recall@K, Reciprocal Rank, Mean Reciprocal Rank, and Hit Rate helpers.
- **Database/configuration** (app/core/) owns PostgreSQL connection lifecycle, pgvector setup, and environment settings.
- **Interfaces/integrations** include FastAPI, Streamable HTTP MCP, Telegram webhook, and n8n workflow templates.

## Quality improvements

The included lexical reranker is a transparent baseline, not a learned cross-encoder. A production deployment can replace it with a cross-encoder or provider reranking API. Evaluation helpers are metric functions; a representative labelled question set is still needed to measure real-world quality.

Scanned-PDF OCR, malware scanning, rate limiting, per-customer API-key provisioning, full per-user tenancy, and backup/restore drills are not included.
