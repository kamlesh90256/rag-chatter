from __future__ import annotations

from dataclasses import dataclass
import logging
import hashlib
from typing import Any

from sqlalchemy import delete
from sqlmodel import Session, select

from backend.ingest.analysis import (
    analyze_hook,
    build_comparison_table,
    calculate_engagement_rate,
    model_dump_json,
)
from backend.ingest.chunking import chunk_transcript
from backend.ingest.embeddings import embed_texts
from backend.ingest.metadata import extract_metadata
from backend.ingest.transcript import extract_transcript
from backend.models.analysis import Analysis
from backend.models.chunk import Chunk
from backend.models.transcript import Transcript
from backend.models.video import Video
from backend.vectorstore.factory import get_repository


@dataclass
class IngestedVideo:
    video: Video
    transcript: Transcript
    chunks: list[Chunk]
    hook_analysis: dict[str, Any]


class IngestionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.vectorstore = get_repository()

    def ingest_pair(self, youtube_url: str, instagram_url: str) -> dict[str, Any]:
        # In production some sources may fail (geo-restrictions, removed videos).
        # Be resilient: attempt each ingest and on failure create a placeholder
        # video record so the rest of the pipeline can continue.
        try:
            video_a = self.ingest_single(youtube_url)
        except Exception as exc:  # pragma: no cover - best-effort
            logger = logging.getLogger("rag_platform.ingest")
            logger.exception("Failed to ingest video A (%s): %s", youtube_url, exc)
            video_a = self._create_placeholder_video(youtube_url, platform="youtube", error=str(exc))
        try:
            video_b = self.ingest_single(instagram_url)
        except Exception as exc:  # pragma: no cover - best-effort
            logger = logging.getLogger("rag_platform.ingest")
            logger.exception("Failed to ingest video B (%s): %s", instagram_url, exc)
            video_b = self._create_placeholder_video(instagram_url, platform="instagram", error=str(exc))
        # ensure dumped video dicts contain numeric metrics for comparison
        va = _serialize_video(video_a["video"])
        vb = _serialize_video(video_b["video"])
        for k in ("likes", "comments", "views"):
            va.setdefault(k, 0)
            vb.setdefault(k, 0)
        # defensive defaults for title used in winner selection
        va.setdefault("title", "Untitled video")
        vb.setdefault("title", "Untitled video")
        engagement = build_comparison_table(va, vb)
        comparison = {
            "engagement_rate": engagement.engagement_rate,
            "winner": engagement.winner,
            "table": engagement.comparison_table,
        }
        analysis = Analysis(
            video_a_id=video_a["video"].id,
            video_b_id=video_b["video"].id,
            engagement_json=model_dump_json(comparison),
            hook_json=model_dump_json(
                {
                    "video_a": video_a["hook_analysis"],
                    "video_b": video_b["hook_analysis"],
                }
            ),
            comparison_json=model_dump_json(comparison),
        )
        self.session.add(analysis)
        self.session.commit()
        self.session.refresh(analysis)
        return {
            "videos": [va, vb],
            "comparison": comparison,
            "hook_analysis": {
                "video_a": video_a["hook_analysis"],
                "video_b": video_b["hook_analysis"],
            },
            "analysis_id": analysis.id,
        }

    def _create_placeholder_video(
    self,
    url: str,
    platform: str,
    error: str | None = None,
) -> dict[str, Any]:
    try:
        metadata = extract_metadata(url, platform) if url else {}
    except Exception:
        metadata = {
            "title": "Unavailable video",
            "creator": "Unknown",
            "raw": {},
        }

    video_id = _canonical_video_id(platform, url)

    # FIX: avoid duplicate inserts
    existing = self.session.get(Video, video_id)

    if existing:
        existing.error_message = error
        self.session.add(existing)
        self.session.commit()
        self.session.refresh(existing)

        return {
            "video": existing,
            "transcript": Transcript(
                video_id=existing.id,
                source_type="unavailable",
                language="en",
                text="",
                is_fallback=True,
            ),
            "chunks": [],
            "hook_analysis": {},
        }

    video = Video(
        id=video_id,
        platform=platform,
        url=url,
        title=metadata.get("title", "Unavailable video"),
        creator=metadata.get("creator", "Unknown"),
        views=0,
        likes=0,
        comments=0,
        follower_count=None,
    )

    video.set_metadata(metadata.get("raw") or {})
    video.error_message = error

    self.session.add(video)
    self.session.commit()
    self.session.refresh(video)

    transcript = Transcript(
        video_id=video.id,
        source_type="unavailable",
        language="en",
        text="",
        is_fallback=True,
    )

    self.session.add(transcript)
    self.session.commit()
    self.session.refresh(transcript)

    return {
        "video": video,
        "transcript": transcript,
        "chunks": [],
        "hook_analysis": {},
    }

    def ingest_single(self, url: str) -> dict[str, Any]:
        from backend.ingest.validator import validate_video_url

        platform = validate_video_url(url)
        metadata = extract_metadata(url, platform)
        video_id = _canonical_video_id(platform, url)
        # Attempt transcript extraction, but do not fail the whole ingest if OpenAI or transcription fails.
        try:
            transcript_payload = extract_transcript(url, platform)
            transcript_text = transcript_payload.get("text", "")
            transcript_source = transcript_payload.get("source_type", "")
            transcript_language = transcript_payload.get("language", "")
            transcript_is_fallback = bool(transcript_payload.get("is_fallback", False))
        except Exception as exc:  # pragma: no cover - best-effort fallback
            transcript_text = ""
            transcript_source = "transcription_failed"
            transcript_language = "en"
            transcript_is_fallback = True
            # preserve the error on metadata to aid debugging
            metadata["transcript_error"] = str(exc)

        transcript = Transcript(
            video_id="",
            source_type=transcript_source,
            language=transcript_language,
            text=transcript_text,
            is_fallback=transcript_is_fallback,
        )
        existing_video = self.session.get(Video, video_id)
        if existing_video:
            video = existing_video
            video.platform = platform
            video.url = url
            video.title = metadata.get("title", "Untitled video")
            video.creator = metadata.get("creator", "Unknown creator")
            video.views = int(metadata.get("views") or 0)
            video.likes = int(metadata.get("likes") or 0)
            video.comments = int(metadata.get("comments") or 0)
            video.upload_date = metadata.get("upload_date")
            video.duration_seconds = int(metadata.get("duration_seconds") or 0) or None
            video.follower_count = metadata.get("follower_count")
            video.set_hashtags(metadata.get("hashtags") or [])
            video.set_metadata(metadata.get("raw") or {})
            video.error_message = None
        else:
            video = Video(
                id=video_id,
                platform=platform,
                url=url,
                title=metadata.get("title", "Untitled video"),
                creator=metadata.get("creator", "Unknown creator"),
                views=int(metadata.get("views") or 0),
                likes=int(metadata.get("likes") or 0),
                comments=int(metadata.get("comments") or 0),
                upload_date=metadata.get("upload_date"),
                duration_seconds=int(metadata.get("duration_seconds") or 0) or None,
                follower_count=metadata.get("follower_count"),
            )
            video.set_hashtags(metadata.get("hashtags") or [])
            video.set_metadata(metadata.get("raw") or {})
            self.session.add(video)
        self.session.commit()
        self.session.refresh(video)

        # Remove prior child rows for idempotent re-ingest of the same video.
        self.session.exec(delete(Transcript).where(Transcript.video_id == video.id))
        self.session.exec(delete(Chunk).where(Chunk.video_id == video.id))
        self.session.commit()

        transcript.video_id = video.id
        self.session.add(transcript)
        self.session.commit()
        self.session.refresh(transcript)
        # If transcript contains itemized segments, use timestamp-aware chunking.
        transcript_items = None
        try:
            transcript_items = transcript_payload.get("items") if "transcript_payload" in locals() else None
        except Exception:
            transcript_items = None

        if transcript_items:
            # itemized transcript: use timestamp-aware chunking
            from backend.ingest.chunking import chunk_transcript_items

            item_chunks = chunk_transcript_items(transcript_items)
            chunks = self._chunk_and_store_with_timestamps(video, item_chunks)
        else:
            # If transcript text is missing, fall back to metadata (description/title)
            # so downstream chunking and embeddings still run and populate the vectorstore.
            if transcript.text:
                chunks = self._chunk_and_store(video, transcript.text)
            else:
                fallback_text = metadata.get("description") or metadata.get("title") or ""
                if fallback_text:
                    chunks = self._chunk_and_store(video, fallback_text)
                else:
                    chunks = []
        first_five_seconds = transcript.text[:300]
        hook = analyze_hook(first_five_seconds, title=video.title)
        return {
            "video": video,
            "transcript": transcript,
            "chunks": chunks,
            "hook_analysis": hook.__dict__,
        }

    def _chunk_and_store(self, video: Video, transcript_text: str) -> list[Chunk]:
        chunk_texts = chunk_transcript(transcript_text)
        if not chunk_texts:
            chunk_texts = [transcript_text]
        # Embed texts, but tolerate embedding API failures and continue storing chunks locally.
        try:
            embeddings = embed_texts(chunk_texts)
        except Exception as exc:  # pragma: no cover - fallback path
            embeddings = []
            # log the embedding failure into the DB by attaching to video's metadata_json
            try:
                current_meta = video.metadata_json or ""
                video.metadata_json = (current_meta or "") + f"\nembed_error: {str(exc)}"
                self.session.add(video)
                self.session.commit()
            except Exception:
                pass
        chunks: list[Chunk] = []
        metadatas: list[dict[str, Any]] = []
        vector_ids: list[str] = []
        # compute synthetic per-chunk timestamps from video.duration_seconds when available
        duration = float(video.duration_seconds) if video.duration_seconds else 60.0
        total = len(chunk_texts) or 1
        per = duration / total if total else duration

        for index, chunk_text in enumerate(chunk_texts, start=1):
            metadata = {
                "video_id": video.id,
                "chunk_id": index,
                "creator": video.creator,
                "title": video.title,
                "url": video.url,
            }
            # add timestamp metadata for chunks generated from raw text
            start_ts = round((index - 1) * per, 3)
            end_ts = round(index * per, 3)
            metadata["timestamp_start"] = start_ts
            metadata["timestamp_end"] = end_ts
            metadatas.append(metadata)
            vector_ids.append(f"{video.id}-{index}")
            chunk = Chunk(
                id=f"{video.id}-{index}",
                video_id=video.id,
                chunk_id=index,
                text=chunk_text,
                creator=video.creator,
                title=video.title,
                url=video.url,
                metadata_json=model_dump_json(metadata),
                timestamp_start=start_ts,
                timestamp_end=end_ts,
                vector_id=vector_ids[-1],
            )
            chunks.append(chunk)
            self.session.add(chunk)
        self.session.commit()
        # Only upsert to vectorstore if embeddings were successfully created and match chunk count.
        if embeddings and len(embeddings) == len(chunk_texts):
            try:
                self.vectorstore.upsert_chunks(
                    texts=chunk_texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=vector_ids,
                )
            except Exception:
                # swallow vectorstore errors to keep ingestion resilient
                pass
        return chunks

    def _chunk_and_store_with_timestamps(self, video: Video, item_chunks: list[dict[str, Any]]) -> list[Chunk]:
        """Store chunks produced by chunk_transcript_items which include timestamps."""
        texts = [c["text"] for c in item_chunks]
        timestamps = [(c.get("timestamp_start"), c.get("timestamp_end")) for c in item_chunks]

        try:
            embeddings = embed_texts(texts)
        except Exception:
            embeddings = []

        chunks: list[Chunk] = []
        metadatas: list[dict[str, Any]] = []
        vector_ids: list[str] = []
        for index, (chunk_obj, (start, end)) in enumerate(zip(item_chunks, timestamps), start=1):
            chunk_text = chunk_obj.get("text", "")
            metadata = {
                "video_id": video.id,
                "chunk_id": index,
                "creator": video.creator,
                "title": video.title,
                "url": video.url,
                "timestamp_start": start,
                "timestamp_end": end,
            }
            metadatas.append(metadata)
            vector_id = f"{video.id}-{index}"
            vector_ids.append(vector_id)
            chunk = Chunk(
                id=vector_id,
                video_id=video.id,
                chunk_id=index,
                text=chunk_text,
                creator=video.creator,
                title=video.title,
                url=video.url,
                metadata_json=model_dump_json(metadata),
                vector_id=vector_id,
                timestamp_start=start,
                timestamp_end=end,
            )
            chunks.append(chunk)
            self.session.add(chunk)
        self.session.commit()

        if embeddings and len(embeddings) == len(texts):
            try:
                self.vectorstore.upsert_chunks(texts=texts, embeddings=embeddings, metadatas=metadatas, ids=vector_ids)
            except Exception:
                pass

        return chunks

    def get_videos(self) -> list[Video]:
        return list(self.session.exec(select(Video).order_by(Video.created_at.desc())))

    def get_sources(self, video_ids: list[str] | None = None) -> list[dict[str, Any]]:
        return self.vectorstore.all_sources(video_ids=video_ids)


def _canonical_video_id(platform: str, url: str) -> str:
    normalized = f"{platform}:{url.strip()}"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest[:24]


def _serialize_video(video: Video) -> dict[str, Any]:
    return {
        "id": video.id,
        "platform": video.platform,
        "url": video.url,
        "title": video.title,
        "creator": video.creator,
        "views": video.views,
        "likes": video.likes,
        "comments": video.comments,
        "upload_date": video.upload_date.isoformat() if video.upload_date else None,
        "duration_seconds": video.duration_seconds,
        "hashtags": video.hashtags,
        "follower_count": video.follower_count,
        "metadata_json": video.metadata_json,
        "error_message": video.error_message,
        "created_at": video.created_at.isoformat(),
    }
