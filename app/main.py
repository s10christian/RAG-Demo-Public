from contextlib import asynccontextmanager
import hmac
import logging
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import initialize_database, get_connection
from app.api.routes.documents import router as documents_router
from app.api.routes.query import router as query_router
from app.api.routes.notion import router as notion_router
from app.services.mcp_server import mcp
from app.services.telegram import handle_telegram_update

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.app_env.lower() == "production" and not settings.rag_api_key:
        raise RuntimeError("RAG_API_KEY must be configured in production")
    initialize_database()
    async with mcp.session_manager.run():
        yield

app = FastAPI(title=settings.app_name, version="1.1.0", description="Authenticated RAG API with Notion workspace sync", lifespan=lifespan)
app.include_router(documents_router, prefix=settings.api_v1_prefix)
app.include_router(query_router, prefix=settings.api_v1_prefix)
app.include_router(notion_router, prefix=settings.api_v1_prefix)

def custom_openapi():
    if app.openapi_schema: return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {"type": "http", "scheme": "bearer", "bearerFormat": "API token", "description": "Use the RAG_API_KEY value as a bearer token."}
    for path, methods in schema.get("paths", {}).items():
        if path.startswith(settings.api_v1_prefix):
            for operation in methods.values():
                if isinstance(operation, dict): operation["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema
app.openapi = custom_openapi

@app.middleware("http")
async def protect_api_and_mcp(request: Request, call_next):
    path = request.url.path
    if path.startswith(settings.api_v1_prefix) or path == "/mcp" or path.startswith("/mcp/"):
        expected = settings.rag_api_key
        if not expected:
            if settings.app_env.lower() == "production": return JSONResponse(status_code=503, content={"detail": "API authentication is not configured"})
        else:
            supplied = request.headers.get("authorization", "")
            token = supplied[7:].strip() if supplied.lower().startswith("bearer ") else request.headers.get("x-api-key", "")
            if not token or not hmac.compare_digest(token, expected): return JSONResponse(status_code=401, content={"detail": "Valid bearer token required"})
    return await call_next(request)

@app.get("/health", tags=["health"])
def health():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur: cur.execute("SELECT 1"); cur.fetchone()
        return {"status": "ok", "database": "connected"}
    except Exception:
        logger.exception("Health check database connection failed")
        raise HTTPException(status_code=503, detail="Database unavailable")

@app.post("/telegram/webhook", include_in_schema=False)
async def telegram_webhook(request: Request, secret: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token")):
    if not settings.telegram_bot_token or not settings.telegram_webhook_secret: raise HTTPException(status_code=503, detail="Telegram integration is not configured")
    if not secret or not hmac.compare_digest(secret, settings.telegram_webhook_secret): raise HTTPException(status_code=401, detail="Invalid webhook secret")
    await handle_telegram_update(await request.json())
    return {"ok": True}

app.mount("/mcp", mcp.streamable_http_app())
