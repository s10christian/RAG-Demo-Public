from functools import lru_cache
from openai import OpenAI
from app.core.config import settings


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured. Add it to the deployment environment.")
    kwargs = {"api_key": settings.openai_api_key, "timeout": 30.0, "max_retries": 2}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**kwargs)


class Embedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = _client().embeddings.create(
            model=settings.embedding_model,
            input=texts,
            dimensions=settings.embedding_dimensions,
        )
        vectors = [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
        if len(vectors) != len(texts):
            raise RuntimeError("Embedding provider returned an unexpected number of vectors")
        if any(len(vector) != settings.embedding_dimensions for vector in vectors):
            raise RuntimeError("Embedding dimensions do not match EMBEDDING_DIMENSIONS")
        return vectors
