from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RAG Demo API"
    app_env: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql://localhost:5432/ragdb"
    openai_api_key: str = ""
    openai_base_url: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    chat_model: str = "gpt-4o-mini"
    rag_api_key: str = ""
    notion_api_key: str = ""
    notion_api_version: str = "2022-06-28"
    tenant_id: str = "default"
    chunk_size: int = 1000
    chunk_overlap: int = 150
    default_top_k: int = 5
    max_top_k: int = 20
    reranker_enabled: bool = False
    reranker_candidate_multiplier: int = 3
    max_upload_size_mb: int = 15
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_allowed_chat_ids: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)

    @property
    def telegram_chat_allowlist(self) -> set[str]:
        return {item.strip() for item in self.telegram_allowed_chat_ids.split(",") if item.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
