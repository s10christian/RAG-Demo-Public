# Vercel deployment

Vercel's Python runtime loads the FastAPI ASGI application using the explicit `[tool.vercel] entrypoint = "app.main:app"` declaration in `pyproject.toml`. No catch-all rewrite is configured, so FastAPI receives original request paths unchanged.

Read [PRODUCTION_RUNBOOK.md](PRODUCTION_RUNBOOK.md) for required environment variables, authentication, API examples, n8n setup, Telegram webhook setup, and verification.

**Production prerequisites:** a Neon PostgreSQL URL, a long random `RAG_API_KEY`, and an OpenAI-compatible `OPENAI_API_KEY`. Store all three as sensitive Vercel environment variables. The application refuses production startup without `RAG_API_KEY`; ingestion and generated answers return a clear configuration error until the model provider key is set.

The app uses Neon for durable state. Never store uploaded files or database files on Vercel's ephemeral filesystem.
