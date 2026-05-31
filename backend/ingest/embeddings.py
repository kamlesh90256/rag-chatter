from __future__ import annotations

from functools import lru_cache
import hashlib
from typing import List

from langchain_openai import OpenAIEmbeddings

from backend.utils.settings import get_settings


def _fallback_embedding(text: str, dim: int = 1536) -> List[float]:
    """Deterministic fallback embedding generator.

    Produces a pseudo-embedding by hashing the text and expanding the hash
    to the requested dimension. This ensures the pipeline can continue
    even when OpenAI is unavailable or returns 401.
    """
    if not text:
        return [0.0] * dim
    out: List[float] = []
    counter = 0
    # concatenate multiple sha256 digests until we have enough bytes
    while len(out) < dim:
        h = hashlib.sha256()
        h.update(text.encode("utf-8"))
        h.update(counter.to_bytes(4, "little", signed=False))
        digest = h.digest()
        for b in digest:
            # map byte to float in [-0.5, 0.5]
            out.append((b / 255.0) - 0.5)
            if len(out) >= dim:
                break
        counter += 1
    return out[:dim]


@lru_cache(maxsize=4)
def get_embeddings_client(api_key: str | None = None) -> OpenAIEmbeddings:
    """Return an OpenAIEmbeddings client cached by api_key.

    Caching is keyed by api_key so that updating OPENAI_API_KEY at runtime
    (without restarting the process) will produce a new client when callers
    pass the current key.
    """
    settings = get_settings()
    key = api_key if api_key is not None else settings.openai_api_key
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    # Attempt to use DB-backed cache for embeddings to avoid re-embedding.
    try:
        import json
        from sqlmodel import Session

        from backend.models.embedding_cache import EmbeddingCache
        from backend.utils.database import engine
        from backend.utils.settings import get_settings as _get_settings

        keys = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in texts]
        cached: dict[str, list[float]] = {}
        with Session(engine) as session:
            rows = session.exec(
                select(EmbeddingCache) if False else None
            )
            # Fallback: do per-key lookup to avoid complex SQL for IN clauses in SQLModel
            for k in keys:
                item = session.get(EmbeddingCache, k)
                if item:
                    try:
                        cached[k] = json.loads(item.vector_json)
                    except Exception:
                        pass

        missing_idx = [i for i, k in enumerate(keys) if k not in cached]
        embeddings: list[list[float]] = [cached[k] for k in keys if k in cached]

        if missing_idx:
            # call embeddings API for missing texts
            client = get_embeddings_client(_get_settings().openai_api_key)
            missing_texts = [texts[i] for i in missing_idx]
            produced = client.embed_documents(missing_texts)
            # store produced embeddings in DB
            try:
                import json
                from sqlmodel import Session
                from backend.utils.database import engine

                with Session(engine) as session:
                    for idx, emb in zip(missing_idx, produced):
                        key = keys[idx]
                        item = EmbeddingCache(key=key, vector_json=json.dumps(emb))
                        session.add(item)
                    session.commit()
            except Exception:
                # swallow cache write errors
                pass

            # build final output in original order
            out: list[list[float]] = []
            produced_map = {keys[idx]: vec for idx, vec in zip(missing_idx, produced)}
            for k in keys:
                if k in cached:
                    out.append(cached[k])
                else:
                    out.append(produced_map.get(k))
            return out

        return [cached[k] for k in keys]
    except Exception:
        # fallback to direct API or deterministic local embeddings
        try:
            from backend.utils.settings import get_settings as _get_settings

            client = get_embeddings_client(_get_settings().openai_api_key)
            return client.embed_documents(texts)
        except Exception:
            dim = 1536
            return [_fallback_embedding(t, dim=dim) for t in texts]


def embed_query(text: str) -> list[float]:
    try:
        # Try cache first
        import json
        from sqlmodel import Session

        from backend.models.embedding_cache import EmbeddingCache
        from backend.utils.database import engine
        from backend.utils.settings import get_settings as _get_settings

        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        with Session(engine) as session:
            item = session.get(EmbeddingCache, key)
            if item:
                try:
                    return json.loads(item.vector_json)
                except Exception:
                    pass

        client = get_embeddings_client(_get_settings().openai_api_key)
        vec = client.embed_query(text)
        try:
            with Session(engine) as session:
                import json

                session.add(EmbeddingCache(key=key, vector_json=json.dumps(vec)))
                session.commit()
        except Exception:
            pass
        return vec
    except Exception:
        return _fallback_embedding(text)
