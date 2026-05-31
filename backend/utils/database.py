from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy import text

from .settings import get_settings

settings = get_settings()

if settings.sqlite_path:
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)


def init_db() -> None:
    from backend.models.analysis import Analysis  # noqa: F401
    from backend.models.chat_history import ChatHistory  # noqa: F401
    from backend.models.chunk import Chunk  # noqa: F401
    from backend.models.transcript import Transcript  # noqa: F401
    from backend.models.video import Video  # noqa: F401
    from backend.models.embedding_cache import EmbeddingCache  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _migrate_sqlite_schema_if_needed()


def _migrate_sqlite_schema_if_needed() -> None:
    """Apply tiny SQLite migrations for older local databases.

    The repo has shipped with pre-existing SQLite files in `data/`, so we
    need to tolerate older schemas when running smoke tests or demo runs.
    """
    if not settings.database_url.startswith("sqlite:///"):
        return

    try:
        with engine.begin() as connection:
            result = connection.execute(text("PRAGMA table_info(chunk)"))
            existing_columns = {row[1] for row in result.fetchall()}
            if "timestamp_start" not in existing_columns:
                connection.execute(text("ALTER TABLE chunk ADD COLUMN timestamp_start FLOAT"))
            if "timestamp_end" not in existing_columns:
                connection.execute(text("ALTER TABLE chunk ADD COLUMN timestamp_end FLOAT"))
    except Exception:
        # Non-fatal: the app can still run with the current schema, but some
        # validation flows may be degraded.
        pass


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


# Ensure database tables exist on import (helps tests and dev runs).
try:
    init_db()
except Exception:
    # If DB init fails here, let application startup handle it normally.
    pass
else:
    # When running tests, ensure embedding cache is cleared to avoid stale vectors
    # interfering with deterministic unit tests that monkeypatch the embeddings client.
    import os
    try:
        # Detect pytest either via env var or if pytest is already imported
        import sys

        if "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules:
            from sqlalchemy import delete
            from backend.models.embedding_cache import EmbeddingCache
            from sqlmodel import Session

            with Session(engine) as session:
                session.exec(delete(EmbeddingCache))
                session.commit()
    except Exception:
        # Non-fatal; proceed if we cannot clear cache
        pass
