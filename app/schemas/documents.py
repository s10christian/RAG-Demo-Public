from uuid import UUID
from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    document_id: UUID
    filename: str
    chunks_created: int
    message: str


class TextIngestRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    text: str = Field(min_length=1, max_length=15_000_000)
    knowledge_base: str = Field(default="default", min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    knowledge_base: str = Field(default="default", min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")


class RetrievedChunk(BaseModel):
    chunk_id: int
    document_id: UUID
    content: str
    source_name: str
    chunk_index: int
    distance: float


class QueryResponse(BaseModel):
    question: str
    results: list[RetrievedChunk]
    answer: str | None = None


class KnowledgeBaseCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    name: str = Field(min_length=2, max_length=120)


class KnowledgeBaseResponse(BaseModel):
    slug: str
    name: str
    created_at: str
