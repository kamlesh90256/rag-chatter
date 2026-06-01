from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from backend.api.schemas import (ChatRequest, ChatResponse, HealthResponse,
                                 IngestRequest)
from backend.graph.workflow import run_workflow
from backend.ingest.pipeline import IngestionService
from backend.models.chat_history import ChatHistory
from backend.models.video import Video
from backend.utils.database import get_session, init_db
from backend.utils.logging import RequestLoggingMiddleware, configure_logging
from backend.utils.security import rate_limit
from backend.utils.settings import get_settings
from backend.api.admin import router as admin_router

settings = get_settings()
configure_logging()
logger = logging.getLogger("rag_platform")

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin routes (protected by ADMIN_SECRET)
app.include_router(admin_router, prefix="/admin")


@app.on_event("startup")
def on_startup() -> None:
    try:
        init_db()
        logger.info("database_initialized")
    except Exception as exc:  # pragma: no cover - defensive startup handling
        logger.exception("startup_failed: %s", exc)
        raise


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.utcnow())


@app.post("/ingest")
def ingest(request: IngestRequest, session: Session = Depends(get_session), _: None = Depends(rate_limit)) -> dict[str, Any]:
    service = IngestionService(session)
    try:
        return service.ingest_pair(request.youtube_url, request.instagram_url)
    except HTTPException:
        raise
    except Exception as exc:
        import traceback

        tb = traceback.format_exc()
        # return richer error detail to assist local debugging (not for prod)
        raise HTTPException(status_code=400, detail={"error": str(exc), "traceback": tb}) from exc


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, session: Session = Depends(get_session), _: None = Depends(rate_limit)):
    try:
        result = run_workflow(request.question, request.thread_id, request.video_ids)
        session.add(ChatHistory(thread_id=request.thread_id, role="user", content=request.question))
        session.add(
            ChatHistory(
                thread_id=request.thread_id,
                role="assistant",
                content=result.answer,
                sources_json=json.dumps(result.citations),
            )
        )
        session.commit()
        if request.stream:
            return StreamingResponse(
                _stream_answer(result.answer, result.citations),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
        return ChatResponse(answer=result.answer, citations=result.citations, thread_id=request.thread_id)
    except HTTPException:
        raise
    except Exception as exc:
        import traceback

        tb = traceback.format_exc()
        # Return richer error detail to assist debugging in production (temporary)
        raise HTTPException(status_code=500, detail={"error": str(exc), "traceback": tb}) from exc


@app.get("/metadata")
def metadata(session: Session = Depends(get_session), video_id: str | None = None) -> dict[str, Any]:
    query = select(Video).order_by(Video.created_at.desc())
    if video_id:
        query = query.where(Video.id == video_id)
    videos = list(session.exec(query))
    return {"videos": [_serialize_video(video) for video in videos]}


@app.get("/sources")
def sources(
    video_id: str | None = None,
    video_ids: str | None = None,
    thread_id: str | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    from backend.graph.workflow import _load_conversation_memory
    from backend.vectorstore.factory import get_repository

    vectorstore = get_repository()
    resolved_ids = [item for item in (video_ids.split(",") if video_ids else [video_id] if video_id else []) if item]
    chunks = vectorstore.all_sources(video_ids=resolved_ids or None)
    if thread_id:
        history = _load_conversation_memory(thread_id, resolved_ids or None)
    else:
        history = ""
    return {"sources": chunks, "memory": history}


def _stream_answer(answer: str, citations: list[dict[str, Any]]):
    payload = {"answer": answer, "citations": citations}
    yield f"data: {json.dumps(payload)}\n\n"
    yield "data: [DONE]\n\n"


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
