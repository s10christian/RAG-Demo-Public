# RAG Demo production runbook

## Architecture
- FastAPI API on Vercel.
- Neon PostgreSQL with pgvector for durable document chunks and embeddings.
- OpenAI-compatible API for embeddings and grounded answer generation.
- Authenticated Streamable HTTP MCP endpoint at `/mcp`.
- Optional Telegram webhook at `/telegram/webhook`.
- n8n workflow templates in `n8n/rag-query-workflow.json` and `n8n/rag-ingest-workflow.json`.

## Required Vercel environment variables
- `APP_ENV=production`
- `LOG_LEVEL=WARNING`
- `DATABASE_URL`: Neon pooled PostgreSQL URI with TLS; store as a **sensitive** Vercel variable.
- `RAG_API_KEY`: long random bearer token; store as a **sensitive** Vercel variable.
- `OPENAI_API_KEY`: provider key for embeddings and answer generation; store as a **sensitive** Vercel variable.

Optional:
- `OPENAI_BASE_URL`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, `CHAT_MODEL`, `TENANT_ID`.
- Telegram requires `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, and `TELEGRAM_ALLOWED_CHAT_IDS`. The allowlist must contain numeric chat IDs; the webhook deliberately ignores all other chats.

## API
- `GET /health` — database health (no authentication required).
- `POST /api/v1/documents` — multipart upload: `file` and optional `knowledge_base`.
- `POST /api/v1/documents/text` — JSON text ingestion: `filename`, `text`, optional `knowledge_base`; accepts .txt/.md.
- `POST /api/v1/query` — JSON: `question`, optional `top_k`, optional `knowledge_base`. Returns both `answer` and retrieved `results`.
- `GET /api/v1/knowledge-bases` — list knowledge bases for configured tenant.
- `POST /api/v1/knowledge-bases` — create a knowledge base.
- `POST /mcp` — MCP Streamable HTTP; use `Authorization: Bearer <RAG_API_KEY>`.

All API and MCP calls require the bearer token in production. The health endpoint and OpenAPI docs are public. Do not place secrets in document content.

## Supported uploads
PDF (text layer), TXT, Markdown, DOCX, CSV, JSON, HTML. Scanned PDFs and image OCR are not supported in the serverless runtime yet.

## n8n
Import both workflow JSON files from the `n8n/` folder. Set n8n environment variables:
- `RAG_API_URL=https://<your-public-domain>`
- `RAG_API_KEY=<same secret as Vercel>`

The query workflow accepts a webhook JSON body such as `{"question":"Summarize the indexed documents"}`. The ingest workflow accepts `{"filename":"notes.txt","text":"Text to index","knowledge_base":"default"}`. Test both with inactive workflows before activating.

## Telegram
Set the three Telegram environment variables above. Register the webhook with Telegram's `setWebhook` method, using `https://<your-public-domain>/telegram/webhook` and the same secret token configured in `TELEGRAM_WEBHOOK_SECRET`. The bot only responds to allowlisted chat IDs. A bot token and chat allowlist are intentionally not guessed or borrowed from unrelated connected bots.

## Deploy and verify
1. Set all required Vercel environment variables as sensitive.
2. Redeploy the production target after every environment change.
3. Check `GET /health` returns HTTP 200 and `{"status":"ok","database":"connected"}`.
4. Check `GET /docs` and `GET /openapi.json`.
5. Call the query endpoint with the bearer token. It should return 503 until `OPENAI_API_KEY` is configured.
6. Upload a small test document, query for a fact in it, and verify the answer cites its source.
7. Initialize an MCP client against `/mcp` with the same bearer token; verify `tools/list` and `tools/call`.
8. Import and test both n8n workflows. Register Telegram only after a dedicated bot token and allowed chat IDs are supplied.

## Security and operations
- Vercel filesystem is ephemeral; all durable state is in Neon.
- Keep `DATABASE_URL`, `RAG_API_KEY`, `OPENAI_API_KEY`, and Telegram credentials in sensitive secret storage.
- Do not log tokens, uploaded document bodies, or provider responses.
- Vercel's serverless runtime scales horizontally; the MCP server is stateless.
- The configured tenant ID is a deployment-level isolation boundary. A separate tenant requires its own deployment configuration/API key; per-customer API-key provisioning is a later enhancement.
- Rate limiting, malware scanning, scanned-PDF OCR, per-user tenancy, backups/restore drills, and production monitoring still require separate operational setup.
