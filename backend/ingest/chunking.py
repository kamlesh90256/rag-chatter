from __future__ import annotations

from typing import Any, List
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.utils.settings import get_settings


def chunk_transcript(text: str) -> list[str]:
    """Backward-compatible: chunk raw text without timestamps."""
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )
    return splitter.split_text(text)


def chunk_transcript_items(items: List[dict[str, Any]]) -> List[dict[str, Any]]:
    """
    Given a list of transcript items with keys 'text', 'start', 'duration',
    produce chunks with aggregated text and timestamp_start/timestamp_end.
    Returns list of dicts: { 'text', 'timestamp_start', 'timestamp_end' }
    """
    settings = get_settings()
    chunks: List[dict[str, Any]] = []
    current_text = []
    current_start = None
    current_end = None
    cur_len = 0

    for item in items:
        t = item.get("text", "")
        start = float(item.get("start") or 0.0)
        duration = float(item.get("duration") or 0.0)
        end = start + duration

        if current_start is None:
            current_start = start

        current_text.append(t)
        current_end = end
        cur_len += len(t)

        # when reached chunk_size, emit chunk
        if cur_len >= settings.chunk_size:
            chunks.append({
                "text": " ".join(current_text).strip(),
                "timestamp_start": current_start,
                "timestamp_end": current_end,
            })
            # overlap handling: keep last overlap chars by naive approach
            overlap_keep = settings.chunk_overlap
            joined = " ".join(current_text)
            if overlap_keep > 0 and len(joined) > overlap_keep:
                tail = joined[-overlap_keep:]
                current_text = [tail]
                cur_len = len(tail)
                # approximate new start as current_end - small epsilon
                current_start = max(current_end - 1.0, start)
            else:
                current_text = []
                cur_len = 0
                current_start = None
            current_end = None

    if current_text:
        chunks.append({
            "text": " ".join(current_text).strip(),
            "timestamp_start": current_start,
            "timestamp_end": current_end,
        })

    return chunks
