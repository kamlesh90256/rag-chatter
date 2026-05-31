from __future__ import annotations

from typing import Any, List
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from backend.utils.settings import get_settings


class QdrantRepository:
    def __init__(self) -> None:
        settings = get_settings()
        url = getattr(settings, "qdrant_url", None)
        api_key = getattr(settings, "qdrant_api_key", None)
        if not url:
            raise RuntimeError("Qdrant URL not configured")
        # QdrantClient will read api_key if provided
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection_name = "video_chunks"
        # ensure collection exists
        try:
            if not self.client.get_collection(self.collection_name):
                pass
        except Exception:
            # create minimal collection (will accept dynamic vectors)
            try:
                self.client.recreate_collection(
                    collection_name=self.collection_name,
                    vectors_config=rest.VectorParams(size=1536, distance=rest.Distance.COSINE),
                )
            except Exception:
                # recreate_collection may fail if already exists concurrently
                pass

    def upsert_chunks(self, *, texts: List[str], embeddings: List[List[float]], metadatas: List[dict[str, Any]], ids: List[str] | None = None) -> List[str]:
        ids = ids or [str(i) for i in range(len(texts))]
        points = []
        for _id, vec, text, meta in zip(ids, embeddings, texts, metadatas):
            payload = dict(meta)
            payload["text"] = text
            points.append(rest.PointStruct(id=_id, vector=vec, payload=payload))
        self.client.upsert(collection_name=self.collection_name, points=points)
        return ids

    def query(self, *, query_embedding: List[float], n_results: int = 6, where: dict[str, Any] | None = None) -> List[dict[str, Any]]:
        filter_expr = None
        if where:
            # simple support for video_id $in
            props = where.get("video_id")
            if isinstance(props, dict) and "$in" in props:
                vals = props["$in"]
                filter_expr = rest.Filter(must=[rest.FieldCondition(key="video_id", match=rest.MatchValue(value=vals))])
        res = self.client.search(collection_name=self.collection_name, query_vector=query_embedding, limit=n_results, filter=filter_expr)
        rows = []
        for item in res:
            payload = item.payload or {}
            rows.append({"text": payload.get("text"), "metadata": payload, "distance": item.score})
        return rows

    def all_sources(self, *, video_ids: List[str] | None = None) -> List[dict[str, Any]]:
        # fetch all points' payloads; for large datasets this should be paginated
        if video_ids:
            filter_expr = rest.Filter(must=[rest.FieldCondition(key="video_id", match=rest.MatchValue(value=video_ids))])
        else:
            filter_expr = None
        # use scroll to fetch payloads
        hits = self.client.scroll(collection_name=self.collection_name, with_payload=True, limit=1000, filter=filter_expr)
        sources = []
        for p in hits:
            payload = p.payload or {}
            sources.append({"text": payload.get("text"), "metadata": payload})
        return sources
