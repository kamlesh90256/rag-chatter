from functools import lru_cache
from pathlib import Path

import json

from pydantic import Field
from pydantic_settings import BaseSettings, EnvSettingsSource, SettingsConfigDict


class _SettingsEnvSource(EnvSettingsSource):
    def prepare_field_value(self, field_name, field, value, value_is_complex):  # type: ignore[override]
        if field_name == "cors_origins" and isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    return [str(item) for item in parsed if str(item).strip()]
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return super().prepare_field_value(field_name, field, value, value_is_complex)


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
    chunk_overlap: int = 200
    # Vector DB selection
    use_qdrant: bool = False
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    # Background worker / queue
    redis_url: str | None = None
    celery_broker_url: str | None = None
    embedding_dim: int = 1536
    retriever_k: int = 6
    admin_secret: str | None = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            _SettingsEnvSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )

    @property
    def sqlite_path(self) -> Path | None:
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", "", 1))
        return None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
