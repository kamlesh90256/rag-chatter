from __future__ import annotations

from typing import Any

from backend.ingest.embeddings import embed_query
from backend.vectorstore.factory import get_repository


class RetrieverService:
    def __init__(self) -> None:
        self.vectorstore = get_repository()

    def retrieve(
        self, question: str, *, video_ids: list[str] | None = None, k: int = 6
    ) -> list[dict[str, Any]]:
        query_embedding = embed_query(question)
        where = {"video_id": {"$in": video_ids}} if video_ids else None
        return self.vectorstore.query(
            query_embedding=query_embedding, n_results=k, where=where
        )
