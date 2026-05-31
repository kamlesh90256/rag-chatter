from pathlib import Path
from typing import Any
from uuid import uuid4

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.utils.settings import get_settings


class ChromaRepository:
    def __init__(self) -> None:
        settings = get_settings()
        settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        # Use unified collection name to match Qdrant adapter
        self.collection = self.client.get_or_create_collection(
            name="video_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(
        self,
        *,
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        ids: list[str] | None = None,
    ) -> list[str]:
        chunk_ids = ids or [str(uuid4()) for _ in texts]
        self.collection.upsert(
            ids=chunk_ids, documents=texts, embeddings=embeddings, metadatas=metadatas
        )
        return chunk_ids

    def query(
        self,
        *,
        query_embedding: list[float],
        n_results: int = 6,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        rows: list[dict[str, Any]] = []
        for index, document in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            rows.append(
                {
                    "text": document,
                    "metadata": metadata,
                    "distance": distances[index] if index < len(distances) else None,
                }
            )
        return rows

    def all_sources(
        self, *, video_ids: list[str] | None = None
    ) -> list[dict[str, Any]]:
        where = {"video_id": {"$in": video_ids}} if video_ids else None
        result = self.collection.get(where=where, include=["documents", "metadatas"])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])
        sources: list[dict[str, Any]] = []
        for index, document in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            sources.append({"text": document, "metadata": metadata})
        return sources
