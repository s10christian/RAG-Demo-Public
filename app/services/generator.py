"""Generates answers using an OpenAI-compatible chat-completions endpoint."""
from functools import lru_cache

from openai import OpenAI

from app.core.config import settings
from app.services.prompt_builder import build_rag_messages


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured. Add it to the deployment environment.")
    kwargs = {"api_key": settings.openai_api_key, "timeout": 45.0, "max_retries": 2}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**kwargs)


def generate_answer(question: str, chunks: list[dict]) -> str:
    if not chunks:
        return "I could not find relevant information in the indexed documents."

    response = _client().chat.completions.create(
        model=settings.chat_model,
        temperature=0.1,
        messages=build_rag_messages(question, chunks),
    )
    answer = response.choices[0].message.content
    return answer.strip() if answer else "The language model returned an empty answer."
