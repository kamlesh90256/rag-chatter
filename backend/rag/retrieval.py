from __future__ import annotations

from typing import Any

from backend.ingest.embeddings import embed_query
from backend.vectorstore.factory import get_repository
import time
from backend.metrics import observe_vector_search, observe_retrieval


class RetrieverService:
    def __init__(self) -> None:
        self.vectorstore = get_repository()

    def retrieve(
        self, question: str, *, video_ids: list[str] | None = None, k: int = 6
    ) -> list[dict[str, Any]]:
        start = time.time()
        query_embedding = embed_query(question)
        where = {"video_id": {"$in": video_ids}} if video_ids else None
        t0 = time.time()
        results = self.vectorstore.query(query_embedding=query_embedding, n_results=k, where=where)
        observe_vector_search(time.time() - t0)
        observe_retrieval(time.time() - start)
        return results
