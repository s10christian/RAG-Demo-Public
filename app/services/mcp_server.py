from mcp.server.fastmcp import FastMCP
from app.core.config import settings
from app.services.rag import answer_question
from app.services.ingestion import ingest_document

mcp = FastMCP(
    "RAG Demo",
    host="0.0.0.0",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
)


@mcp.tool()
def search_knowledge_base(question: str, knowledge_base: str = "default", top_k: int = 5) -> dict:
    """Search indexed documents and return a grounded answer with source passages."""
    if len(question.strip()) < 3:
        raise ValueError("Question must contain at least 3 characters")
    answer, sources = answer_question(question, min(max(top_k, 1), settings.max_top_k), knowledge_base)
    return {"answer": answer, "sources": sources}


@mcp.tool()
def ingest_text_document(filename: str, text: str, knowledge_base: str = "default") -> dict:
    """Index plain text content as a document in the selected knowledge base."""
    if not filename.lower().endswith((".txt", ".md")):
        raise ValueError("MCP text ingestion accepts .txt and .md filenames only")
    if not text.strip() or len(text.encode("utf-8")) > settings.max_upload_size_mb * 1024 * 1024:
        raise ValueError("Text is empty or exceeds the upload size limit")
    document_id, chunks = ingest_document(filename, text.encode("utf-8"), knowledge_base)
    return {"document_id": document_id, "chunks_created": chunks}
