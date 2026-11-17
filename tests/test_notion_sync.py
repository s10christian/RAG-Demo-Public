import pytest

from app.services.notion_sync import (
    _blocks,
    _document_body,
    _page_properties,
    _plain,
    _property_text,
    _title,
)


def test_database_properties_are_serialized_with_labels():
    page = {
        "properties": {
            "Name": {"type": "title", "title": [{"plain_text": "Release 4"}]},
            "Status": {"type": "status", "status": {"name": "In progress"}},
            "Priority": {"type": "select", "select": {"name": "High"}},
            "Tags": {"type": "multi_select", "multi_select": [{"name": "RAG"}, {"name": "Notion"}]},
            "Due": {"type": "date", "date": {"start": "2026-11-20", "end": "2026-11-21"}},
            "Estimate": {"type": "number", "number": 13},
            "Done": {"type": "checkbox", "checkbox": True},
            "Owner": {"type": "people", "people": [{"name": "Alex", "id": "user-1"}]},
            "Website": {"type": "url", "url": "https://example.test"},
            "API Token": {"type": "rich_text", "rich_text": [{"plain_text": "must-not-index"}]},
        }
    }
    rendered = _page_properties(page)
    for expected in ("Name: Release 4", "Status: In progress", "Priority: High",
                     "Tags: RAG, Notion", "Due: 2026-11-20 to 2026-11-21",
                     "Estimate: 13", "Done: True", "Owner: Alex", "Website: https://example.test"):
        assert expected in rendered
    assert "must-not-index" not in rendered


def test_table_row_cells_are_extracted():
    block = {"type": "table_row", "table_row": {"cells": [
        [{"plain_text": "Environment"}],
        [{"plain_text": "Production"}],
        [{"plain_text": "Healthy"}],
    ]}}
    assert _plain(block) == "Environment | Production | Healthy"


def test_common_blocks_and_nested_content_are_extracted():
    assert _plain({"type": "callout", "callout": {"rich_text": [{"plain_text": "Important note"}]}}) == "Important note"
    assert _plain({"type": "equation", "equation": {"expression": "x + y"}}) == "x + y"
    assert _plain({"type": "bookmark", "bookmark": {"url": "https://example.test"}}) == "https://example.test"

    class FakeClient:
        pass

    calls = []
    def fake_request(client, method, path, **kwargs):
        calls.append((path, kwargs.get("params", {})))
        if len(calls) == 1:
            return {"results": [
                {"id": "table-row", "type": "table_row", "table_row": {"cells": [[{"plain_text": "A"}], [{"plain_text": "B"}]]}},
                {"id": "child", "type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Nested"}]}, "has_children": True},
            ], "has_more": True, "next_cursor": "next"}
        if len(calls) == 2:
            return {"results": [{"id": "nested", "type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Child text"}]}}], "has_more": False}
        return {"results": [{"id": "last", "type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Page two"}]}}], "has_more": False}

    import app.services.notion_sync as sync
    original = sync._request
    sync._request = fake_request
    try:
        result = _blocks(FakeClient(), "root")
    finally:
        sync._request = original

    assert "A | B" in result
    assert "Nested" in result
    assert "Child text" in result
    assert "Page two" in result
    assert calls[-1][1].get("start_cursor") == "next"


def test_page_title_and_document_body_include_database_fields():
    page = {
        "id": "page-id",
        "url": "https://notion.so/page-id",
        "last_edited_time": "2026-11-15T12:00:00Z",
        "properties": {
            "Task": {"type": "title", "title": [{"plain_text": "Deploy RAG"}]},
            "Status": {"type": "status", "status": {"name": "Ready"}},
        },
    }
    title = _title(page)
    body = _document_body(page, title, "A table value")
    assert title == "Deploy RAG"
    assert "Status: Ready" in body
    assert "A table value" in body
    assert page["url"] in body


def test_secret_named_properties_are_not_indexed():
    assert _property_text("Password", {"type": "rich_text", "rich_text": [{"plain_text": "secret"}]}) == ""


def test_formula_and_rollup_numeric_values_are_serialized():
    assert _property_text("Calculated", {
        "type": "formula", "formula": {"type": "number", "number": 42}
    }) == "Calculated: 42"
    assert _property_text("Total", {
        "type": "rollup", "rollup": {"type": "number", "number": 7}
    }) == "Total: 7"
