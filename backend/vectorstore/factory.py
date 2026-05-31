from __future__ import annotations

from typing import Any

from backend.utils.settings import get_settings


def get_repository() -> Any:
    settings = get_settings()
    use_qdrant = getattr(settings, "use_qdrant", False)
    if use_qdrant:
        try:
            from backend.vectorstore.qdrant import QdrantRepository

            return QdrantRepository()
        except Exception as exc:
            # fallback to chroma if qdrant import/config fails
            from backend.vectorstore.chroma import ChromaRepository

            return ChromaRepository()
    else:
        from backend.vectorstore.chroma import ChromaRepository

        return ChromaRepository()
