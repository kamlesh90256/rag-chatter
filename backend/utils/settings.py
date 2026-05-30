from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Creator Video Intelligence RAG Platform"
    api_v1_prefix: str = "/api"
    environment: str = "development"
    log_level: str = "INFO"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    database_url: str = "sqlite:///./data/app.db"
    chroma_persist_dir: Path = Field(default=Path("./data/chroma"))
    rate_limit_per_minute: int = 60
    request_timeout_seconds: int = 120
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    max_chat_history_turns: int = 12
    chunk_size: int = 800
    chunk_overlap: int = 100
    retriever_k: int = 6

    @property
    def sqlite_path(self) -> Path | None:
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", "", 1))
        return None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
