from functools import lru_cache
from pathlib import Path
import os

from pydantic import Field, field_validator
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
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ]
    )

    @field_validator("cors_origins", mode="before")
    def _parse_cors_origins(cls, v):
        # Accept an env string (JSON list or comma-separated) or an empty value.
        if v is None:
            return v
        if isinstance(v, str):
            s = v.strip()
            if s == "":
                return [
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                    "http://localhost:3001",
                    "http://127.0.0.1:3001",
                ]
            # try json
            try:
                import json

                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                # fallback to comma-split
                return [part.strip() for part in s.split(",") if part.strip()]
        return v
    max_chat_history_turns: int = 12
    chunk_size: int = 800
    chunk_size: int = 1000
    chunk_overlap: int = 200
    # Vector DB selection
    use_qdrant: bool = False
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    # Background worker / queue
    redis_url: str | None = None
    celery_broker_url: str | None = None
    # Embedding model
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    retriever_k: int = 6
    admin_secret: str | None = None

    @property
    def sqlite_path(self) -> Path | None:
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", "", 1))
        return None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Some CI environments set an empty string for CORS_ORIGINS which
    # pydantic tries to json-decode and fails. If the env var is present
    # but empty, remove it so Settings uses the default value.
    try:
        val = os.environ.get("CORS_ORIGINS")
        if val is not None:
            s = val.strip()
            if s == "":
                # remove empty
                del os.environ["CORS_ORIGINS"]
            else:
                # If it's not a JSON list, normalize into a JSON array so
                # pydantic's EnvSettingsSource (which json.loads) will succeed.
                if not s.startswith("["):
                    # split on commas to support simple comma-separated values
                    parts = [p.strip() for p in s.split(",") if p.strip()]
                    import json

                    os.environ["CORS_ORIGINS"] = json.dumps(parts)
    except Exception:
        pass
    return Settings()
