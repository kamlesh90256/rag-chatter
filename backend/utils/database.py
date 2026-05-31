from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

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


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
