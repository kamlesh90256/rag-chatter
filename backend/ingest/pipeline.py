from __future__ import annotations

from dataclasses import dataclass
import logging
import hashlib
from typing import Any

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
        va = video_a["video"].model_dump()
        vb = video_b["video"].model_dump()
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
            "videos": [video_a["video"].model_dump(), video_b["video"].model_dump()],
            "comparison": comparison,
            "hook_analysis": {
                "video_a": video_a["hook_analysis"],
                "video_b": video_b["hook_analysis"],
            },
            "analysis_id": analysis.id,
        }

    def _create_placeholder_video(self, url: str, platform: str, error: str | None = None) -> dict[str, Any]:
        # Create a minimal Video record to ensure downstream flows have an ID to reference.
        # Be defensive: metadata extraction may fail (eg. yt-dlp sign-in required).
        try:
            metadata = extract_metadata(url, platform) if url else {}
        except Exception:  # pragma: no cover - best-effort fallback
            metadata = {"title": "Unavailable video", "creator": "Unknown", "raw": {}}
        video_id = _canonical_video_id(platform, url)
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
        # create an empty transcript record to keep schema expectations
        transcript = Transcript(video_id=video.id, source_type="unavailable", language="en", text="", is_fallback=True)
        self.session.add(transcript)
        self.session.commit()
        self.session.refresh(transcript)
        return {"video": video, "transcript": transcript, "chunks": [], "hook_analysis": {}}

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

        transcript.video_id = video.id
        self.session.add(transcript)
        self.session.commit()
        self.session.refresh(transcript)
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
        for index, chunk_text in enumerate(chunk_texts, start=1):
            metadata = {
                "video_id": video.id,
                "chunk_id": index,
                "creator": video.creator,
                "title": video.title,
                "url": video.url,
            }
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

    def get_videos(self) -> list[Video]:
        return list(self.session.exec(select(Video).order_by(Video.created_at.desc())))

    def get_sources(self, video_ids: list[str] | None = None) -> list[dict[str, Any]]:
        return self.vectorstore.all_sources(video_ids=video_ids)


def _canonical_video_id(platform: str, url: str) -> str:
    normalized = f"{platform}:{url.strip()}"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest[:24]
