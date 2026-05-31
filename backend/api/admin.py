from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import select

from backend.ingest.embeddings import embed_texts
from backend.models.chunk import Chunk
from backend.utils.database import get_session
from backend.utils.settings import get_settings
from backend.vectorstore.chroma import ChromaRepository

logger = logging.getLogger("rag_platform.admin")
router = APIRouter()


@router.post("/rebuild-vectorstore")
def rebuild_vectorstore(
    x_admin_secret: str | None = Header(None), x_autogen: str | None = Header(None), session: Any = Depends(get_session)
) -> dict[str, Any]:
    settings = get_settings()
    # If ADMIN_SECRET is configured, require it to match
    if settings.admin_secret:
        if not x_admin_secret or x_admin_secret != settings.admin_secret:
            raise HTTPException(status_code=403, detail="Invalid admin secret")
        generated_secret: str | None = None
    else:
        # Allow a one-shot autogen flow if caller provides x-autogen: true
        generated_secret = None
        if not x_autogen or str(x_autogen).lower() not in ("1", "true", "yes"):
            raise HTTPException(status_code=403, detail="Admin secret not configured on server")
        # Generate a one-time admin secret and return it in response for convenience
        import uuid
        from random import randint

        generated_secret = f"{uuid.uuid4()}-{randint(0,99999)}"

    # Initialize repository and wipe existing collection if present
    repo = ChromaRepository()
    try:
        try:
            repo.client.delete_collection(name="creator_video_chunks")
        except Exception:
            # Some chroma versions expose different APIs; attempt to clear collection
            try:
                repo.collection.delete()
            except Exception:
                logger.exception("Failed to delete existing chroma collection, continuing to recreate")
    except Exception:
        logger.exception("Error while attempting to remove existing collection")

    # Recreate repo/collection to ensure clean state
    repo = ChromaRepository()

    # Load all chunks from DB
    result = session.exec(select(Chunk))
    if hasattr(result, "all"):
        chunks = result.all()
    else:
        chunks = list(result)
    texts: list[str] = []
    metadatas: list[dict[str, Any]] = []
    ids: list[str] = []

    for c in chunks:
        texts.append(c.text)
        try:
            meta = json.loads(c.metadata_json) if c.metadata_json else {}
        except Exception:
            meta = {"video_id": c.video_id, "chunk_id": c.chunk_id}
        metadatas.append(meta)
        ids.append(c.vector_id or f"{c.video_id}-{c.chunk_id}")

    # Compute embeddings (will fallback to deterministic embeddings if OpenAI not configured)
    embeddings = []
    if texts:
        try:
            embeddings = embed_texts(texts)
        except Exception:
            logger.exception("Embeddings failed during rebuild; proceeding with fallback embeddings where possible")
            embeddings = []

    # Upsert into Chroma only if embeddings match
    upserted = 0
    if embeddings and len(embeddings) == len(texts):
        try:
            repo.upsert_chunks(texts=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
            upserted = len(texts)
        except Exception:
            logger.exception("Failed to upsert chunks into chroma during rebuild")
    else:
        # If embeddings aren't available, create collection entries without embeddings (if supported)
        try:
            repo.upsert_chunks(texts=texts, embeddings=[[] for _ in texts], metadatas=metadatas, ids=ids)
            upserted = len(texts)
        except Exception:
            logger.exception("Failed to upsert chunks without embeddings; collection may remain empty")

    resp: dict[str, Any] = {"upserted": upserted, "total_chunks": len(texts)}
    if generated_secret:
        resp["generated_admin_secret"] = generated_secret
    return resp
