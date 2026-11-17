from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.schemas.documents import QueryRequest, QueryResponse
from app.services.rag import answer_question

router = APIRouter(tags=["retrieval"])


@router.post("/query", response_model=QueryResponse)
def query_documents(payload: QueryRequest):
    try:
        answer, results = answer_question(
            payload.question, payload.top_k or settings.default_top_k, payload.knowledge_base
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="RAG query failed") from exc
    return QueryResponse(question=payload.question, results=results, answer=answer)
