from __future__ import annotations

from typing import Any


def build_context(chunks: list[dict[str, Any]]) -> str:
    sections: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        sections.append(
            f"[Source {index}] {metadata.get('title', 'Unknown title')} | Chunk {metadata.get('chunk_id', index)}\n"
            f"Creator: {metadata.get('creator', 'Unknown creator')}\n"
            f"URL: {metadata.get('url', '')}\n"
            f"Text: {chunk.get('text', '')}"
        )
    return "\n\n".join(sections)
