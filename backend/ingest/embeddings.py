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
    try:
        from backend.utils.settings import get_settings as _get_settings

        client = get_embeddings_client(_get_settings().openai_api_key)
        return client.embed_documents(texts)
    except Exception:
        # fallback to deterministic local embeddings
        dim = 1536
        return [_fallback_embedding(t, dim=dim) for t in texts]


def embed_query(text: str) -> list[float]:
    try:
        from backend.utils.settings import get_settings as _get_settings

        client = get_embeddings_client(_get_settings().openai_api_key)
        return client.embed_query(text)
    except Exception:
        return _fallback_embedding(text)
