# RAG Demo — modular Retrieval-Augmented Generation platform

A modular RAG API built with FastAPI, PostgreSQL/pgvector, an OpenAI-compatible embedding and chat interface, Streamable HTTP MCP, optional Telegram, and n8n workflow templates.

## RAG architecture

### Document ingestion
1. **Ingestion API** validates files and requests.
2. **Extractor** converts PDF, TXT, Markdown, DOCX, CSV, JSON, and HTML to text.
3. **Chunker** splits text into overlapping passages.
4. **Embedder** converts passages into vectors.
5. **Vector store** persists documents, metadata, chunks, and vectors in PostgreSQL/pgvector.

### Retrieval and generation
1. **Retriever** embeds the question and finds similar chunks within the tenant and knowledge-base scope.
2. **Optional reranker** improves candidate ordering with a lightweight lexical relevance score. Disabled by default; set RERANKER_ENABLED=true to enable it.
3. **Prompt builder** creates grounded prompts and treats retrieved documents as reference data.
4. **Generator** produces an answer from retrieved evidence and adds source citations.
5. **Evaluation helpers** calculate Precision@K, Recall@K, Reciprocal Rank, Mean Reciprocal Rank, and Hit Rate.

See docs/RAG_PIPELINE.md and docs/ARCHITECTURE.md for module responsibilities and flow.

## Production deployment

The API is deployed on Vercel and uses Neon for persistent storage. Configure these **sensitive** environment variables:
- **DATABASE_URL** — Neon pooled PostgreSQL URI with TLS.
- **RAG_API_KEY** — bearer token protecting API and MCP endpoints.
- **OPENAI_API_KEY** — key for the configured OpenAI-compatible embedding and chat provider.

Also set APP_ENV=production and LOG_LEVEL=WARNING. The provider can use a compatible endpoint by setting OPENAI_BASE_URL; select model IDs supported by that provider. See docs/PRODUCTION_RUNBOOK.md.

## API endpoints
- GET /health — public database health.
- POST /api/v1/documents — upload supported files as multipart form data.
- POST /api/v1/documents/text — ingest .txt or .md content from JSON.
- POST /api/v1/query — retrieve relevant passages and generate a grounded answer.
- GET /api/v1/knowledge-bases and POST /api/v1/knowledge-bases.
- MCP Streamable HTTP: /mcp.
- Optional Telegram webhook: /telegram/webhook.

All /api/v1/* and /mcp requests require Authorization: Bearer <RAG_API_KEY>. Health and API documentation are public.

## n8n

Import both workflow templates:
- n8n/rag-query-workflow.json — webhook-triggered RAG question.
- n8n/rag-ingest-workflow.json — webhook-triggered text ingestion.

Configure n8n environment variables RAG_API_URL and RAG_API_KEY. See the production runbook for request examples.

## Telegram

Telegram support is optional. It requires a dedicated bot token, webhook secret, and explicit allowed chat IDs. No bot token is committed or borrowed from another integration.

## Local development

    cp .env.example .env
    # Set DATABASE_URL, RAG_API_KEY, and OPENAI_API_KEY in .env
    docker compose up --build

Open http://localhost:8000/docs.

## Tests

    pip install -r requirements.txt
    pytest -q

## Explicit limitations

The lexical reranker is a baseline, not a learned cross-encoder. OCR for scanned PDFs, malware scanning, rate limiting, per-customer API-key provisioning, full per-user tenancy, backup/restore drills, and production monitoring require separate implementation or configuration.


## Quick start (local development)

1. Copy `.env.example` to `.env`.
2. Replace `POSTGRES_PASSWORD` with a long, unique random password. Set `DATABASE_URL` to use the same password.
3. Set `RAG_API_KEY` and the provider keys you intend to use. Keep optional integrations blank until configured.
4. Start the stack with `docker compose up --build`.
5. Open `http://localhost:8000/docs` for the API documentation.

Never commit `.env`, real API keys, database URLs, Telegram bot tokens, webhook secrets, Notion tokens, customer documents, or production data. The included `.env.example` contains placeholders only. The Docker Compose database and API ports are bound to localhost for development; configure production networking, TLS, secret management, backups, and access controls separately.

## Public distribution

This repository is a clean source snapshot. It intentionally does not include the original development repository's Git history, deployments, secrets, private data, or runtime state. Review `SECURITY.md` before deploying or contributing.
