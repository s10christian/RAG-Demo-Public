"""Sync all Notion pages and database rows shared with this integration into RAG."""
from __future__ import annotations

import re
import time
from hashlib import sha256
from uuid import NAMESPACE_URL, uuid5

import httpx

from app.core.config import settings
from app.services.ingestion import ingest_document

API = "https://api.notion.com/v1"
_SECRET_NAME = re.compile(r"(password|passwd|secret|token|api.?key|credential|private.?key)", re.I)


def _request(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    """Retry transient Notion rate-limit/server responses; fail clearly otherwise."""
    for attempt in range(4):
        response = client.request(method, API + path, **kwargs)
        if response.status_code == 429 or response.status_code >= 500:
            if attempt == 3:
                response.raise_for_status()
            retry_after = response.headers.get("Retry-After")
            try:
                delay = min(float(retry_after), 30.0) if retry_after else 2 ** attempt
            except ValueError:
                delay = 2 ** attempt
            time.sleep(delay)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError("Notion request retry limit reached")


def _rich_text(items) -> str:
    if isinstance(items, str):
        return items
    if not isinstance(items, list):
        return ""
    return "".join(
        item.get("plain_text") or item.get("text", {}).get("content", "")
        for item in items if isinstance(item, dict)
    )


def _value_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return ", ".join(filter(None, (_value_text(item) for item in value)))
    if not isinstance(value, dict):
        return ""
    if "plain_text" in value:
        return str(value.get("plain_text") or "")
    value_type = value.get("type")
    if value_type and value_type in value:
        return _value_text(value.get(value_type))
    if "name" in value:
        return str(value.get("name") or "")
    if "title" in value:
        return _rich_text(value.get("title"))
    if "start" in value:
        return " to ".join(filter(None, (str(value.get("start") or ""), str(value.get("end") or ""))))
    if "id" in value:
        return str(value["id"])
    return ""


def _property_text(name: str, prop: dict) -> str:
    """Render Notion database property values without losing their property labels."""
    if _SECRET_NAME.search(name or ""):
        return ""
    if not isinstance(prop, dict):
        return ""
    kind = prop.get("type", "")
    value = prop.get(kind) if kind else None
    if kind in {"title", "rich_text"}:
        rendered = _rich_text(value)
    elif kind in {"number", "checkbox", "url", "email", "phone_number", "created_time", "last_edited_time"}:
        rendered = "" if value is None else str(value)
    elif kind in {"select", "status"}:
        rendered = _value_text(value)
    elif kind == "multi_select":
        rendered = ", ".join(x.get("name", "") for x in (value or []) if isinstance(x, dict))
    elif kind in {"people", "relation"}:
        rendered = ", ".join(_value_text(x) for x in (value or []) if isinstance(x, dict))
    elif kind == "date":
        rendered = _value_text(value)
    elif kind == "formula":
        rendered = _value_text(value)
    elif kind == "rollup":
        if isinstance(value, dict) and value.get("type") == "array":
            rendered = ", ".join(_value_text(x) for x in value.get("array", []))
        elif isinstance(value, dict):
            rendered = _value_text(value.get(value.get("type", ""), value))
        else:
            rendered = _value_text(value)
    elif kind in {"created_by", "last_edited_by"}:
        rendered = _value_text(value)
    elif kind == "files":
        rendered = ", ".join(
            filter(None, (f.get("name", "") or f.get("external", {}).get("url", "") or f.get("file", {}).get("url", "") for f in (value or []) if isinstance(f, dict)))
        )
    elif kind == "unique_id":
        rendered = f"{value.get('prefix', '') or ''}{value.get('number', '')}" if isinstance(value, dict) else _value_text(value)
    elif kind == "place":
        rendered = _value_text(value)
    else:
        rendered = _value_text(value)
    return f"{name}: {rendered}" if rendered else ""


def _page_properties(page: dict) -> str:
    lines = []
    for name, prop in (page.get("properties") or {}).items():
        line = _property_text(name, prop)
        if line:
            lines.append(line)
    return "\n".join(lines)


def _plain(block: dict) -> str:
    """Extract text from common Notion block types, including table rows."""
    typ = block.get("type", "")
    value = block.get(typ, {}) or {}
    text = _rich_text(value.get("rich_text") or value.get("title") or value.get("caption") or [])
    if typ == "table_row":
        cells = value.get("cells") or []
        text = " | ".join(_rich_text(cell) for cell in cells)
    elif typ in {"bookmark", "embed", "link_preview"}:
        text = "\n".join(filter(None, (text, value.get("url", ""))))
    elif typ in {"file", "pdf", "image", "audio", "video"}:
        file_obj = value.get("file") or value.get("external") or {}
        text = "\n".join(filter(None, (value.get("name", ""), text, file_obj.get("url", ""))))
    elif typ in {"child_page", "child_database"}:
        text = value.get("title", text)
    elif typ == "equation":
        text = value.get("expression", text)
    return str(text or "").strip()


def _blocks(client: httpx.Client, block_id: str, depth: int = 0) -> str:
    if depth > 8:
        return ""
    parts, cursor = [], None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        data = _request(client, "GET", f"/blocks/{block_id}/children", params=params)
        for block in data.get("results", []):
            line = _plain(block)
            if line:
                parts.append(line)
            if block.get("has_children"):
                nested = _blocks(client, block["id"], depth + 1)
                if nested:
                    parts.append(nested)
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return "\n".join(parts)


def _title(obj: dict) -> str:
    props = obj.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "title":
            return _rich_text(prop.get("title")) or "Untitled"
    # Search results for ordinary pages can expose a direct title field.
    return _rich_text(obj.get("title")) or "Untitled"


def _search_all(client: httpx.Client, kind: str) -> list[dict]:
    out, cursor = [], None
    while True:
        body = {"page_size": 100, "filter": {"property": "object", "value": kind}}
        if cursor:
            body["start_cursor"] = cursor
        data = _request(client, "POST", "/search", json=body)
        out.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return out


def _document_body(page: dict, title: str, block_text: str) -> str:
    pid = page.get("id", "")
    properties = _page_properties(page)
    url = page.get("url", "")
    parts = [
        f"Title: {title}",
        f"Notion URL: {url}",
        f"Page ID: {pid}",
        f"Last edited: {page.get('last_edited_time', '')}",
    ]
    if properties:
        parts.extend(["Database properties:", properties])
    if block_text.strip():
        parts.extend(["Page content:", block_text])
    return "\n".join(parts)


def sync_notion_workspace() -> dict:
    if not settings.notion_api_key:
        raise RuntimeError("NOTION_API_KEY is not configured")
    headers = {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Notion-Version": settings.notion_api_version,
        "Content-Type": "application/json",
    }
    pages_indexed = chunks = unchanged = errors = 0
    error_details, sources = [], []
    with httpx.Client(headers=headers, timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        # Search failures are fatal: never report a successful partial workspace discovery.
        pages = _search_all(client, "page")
        databases = _search_all(client, "database")
        for db in databases:
            cursor = None
            while True:
                body = {"page_size": 100}
                if cursor:
                    body["start_cursor"] = cursor
                try:
                    data = _request(client, "POST", f"/databases/{db['id']}/query", json=body)
                except httpx.HTTPError as exc:
                    errors += 1
                    error_details.append({"database_id": db.get("id"), "error": type(exc).__name__})
                    break
                pages.extend(data.get("results", []))
                if not data.get("has_more"):
                    break
                cursor = data.get("next_cursor")
                if not cursor:
                    break

        seen = set()
        for page in pages:
            pid = page.get("id")
            if not pid or pid in seen or page.get("archived") or page.get("in_trash"):
                continue
            seen.add(pid)
            try:
                title = _title(page)
                block_text = _blocks(client, pid)
                body = _document_body(page, title, block_text)
                name = f"notion-{title[:100]}-{pid.replace('-', '')[:8]}.md"
                doc_id = str(uuid5(NAMESPACE_URL, f"notion:{pid}"))
                raw = body.encode("utf-8")
                from app.services.vector_store import PgVectorStore
                if PgVectorStore().has_document(doc_id, sha256(raw).hexdigest()):
                    unchanged += 1
                else:
                    _, count = ingest_document(name, raw, document_id=doc_id)
                    pages_indexed += 1
                    chunks += count
                sources.append({"page_id": pid, "title": title, "url": page.get("url", "")})
            except Exception as exc:
                errors += 1
                error_details.append({"page_id": pid, "error": type(exc).__name__})
    return {
        "discovered_pages_and_rows": len(seen),
        "indexed_or_updated": pages_indexed,
        "unchanged": unchanged,
        "chunks_created": chunks,
        "errors": errors,
        "error_details": error_details[:50],
        "sources": sources,
    }
