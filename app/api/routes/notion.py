from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.services.notion_sync import sync_notion_workspace

router = APIRouter(tags=["notion"] )

@router.post("/notion/sync")
def sync_notion():
    if not settings.notion_api_key:
        raise HTTPException(status_code=503, detail="Notion integration is not configured")
    try:
        return sync_notion_workspace()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Notion sync failed; check integration access and application logs") from exc
