from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.core.config import settings
from app.core.database import get_connection
from app.schemas.documents import IngestResponse, KnowledgeBaseCreate, KnowledgeBaseResponse, TextIngestRequest
from app.services.ingestion import ingest_document

router = APIRouter(tags=["documents"])


def _ingest(filename: str, content: bytes, knowledge_base: str) -> IngestResponse:
    try:
        document_id, count = ingest_document(filename, content, knowledge_base)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Document ingestion failed") from exc
    return IngestResponse(
        document_id=document_id, filename=filename, chunks_created=count,
        message="Document ingested and indexed successfully",
    )


@router.post("/documents", response_model=IngestResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    knowledge_base: str = Form(default="default", min_length=1, max_length=64),
):
    filename = (file.filename or "upload").replace("\\", "/").split("/")[-1]
    if not filename or len(filename) > 255:
        raise HTTPException(status_code=400, detail="Invalid filename")
    content = await file.read(settings.max_upload_size_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds the configured upload limit")
    return _ingest(filename, content, knowledge_base)


@router.post("/documents/text", response_model=IngestResponse, status_code=201)
def ingest_text_document(payload: TextIngestRequest):
    filename = Path(payload.filename.replace("\\", "/")).name
    if Path(filename).suffix.lower() not in {".txt", ".md"}:
        raise HTTPException(status_code=400, detail="Text ingestion accepts .txt and .md filenames only")
    content = payload.text.encode("utf-8")
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Text exceeds the configured upload limit")
    return _ingest(filename, content, payload.knowledge_base)


@router.post("/knowledge-bases", response_model=KnowledgeBaseResponse, status_code=201)
def create_knowledge_base(payload: KnowledgeBaseCreate):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO knowledge_bases (tenant_id, slug, name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (tenant_id, slug) DO NOTHING
                    RETURNING slug, name, created_at
                """, (settings.tenant_id, payload.slug, payload.name))
                row = cur.fetchone()
                if row is None:
                    cur.execute("""
                        SELECT slug, name, created_at FROM knowledge_bases
                        WHERE tenant_id = %s AND slug = %s
                    """, (settings.tenant_id, payload.slug))
                    row = cur.fetchone()
        return KnowledgeBaseResponse(slug=row[0], name=row[1], created_at=row[2].isoformat())
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Knowledge base operation failed") from exc


@router.get("/knowledge-bases", response_model=list[KnowledgeBaseResponse])
def list_knowledge_bases():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT slug, name, created_at FROM knowledge_bases
                WHERE tenant_id = %s ORDER BY created_at
            """, (settings.tenant_id,))
            rows = cur.fetchall()
    return [KnowledgeBaseResponse(slug=r[0], name=r[1], created_at=r[2].isoformat()) for r in rows]
