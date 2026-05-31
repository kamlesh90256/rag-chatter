from __future__ import annotations

import json
import logging
from datetime import datetime
import time
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import openai
from typing import Generator
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
from backend.metrics import metrics_response, REQUEST_COUNT, REQUEST_LATENCY

settings = get_settings()
configure_logging()
logger = logging.getLogger("rag_platform")

# If `CORS` origins were passed via env as a JSON string, coerce to list
if isinstance(settings.cors_origins, str):
    try:
        parsed = json.loads(settings.cors_origins)
        settings.cors_origins = parsed if isinstance(parsed, list) else [parsed]
    except Exception:
        settings.cors_origins = [settings.cors_origins]

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


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as exc:
        status = 500
        raise
    finally:
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, http_status=str(status)).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(time.time() - start)
    return response


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


@app.get("/metrics")
def metrics():
    try:
        payload, content_type = metrics_response()
        return Response(content=payload, media_type=content_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ingest")
def ingest(request: IngestRequest, session: Session = Depends(get_session), _: None = Depends(rate_limit)) -> dict[str, Any]:
    service = IngestionService(session)
    try:
        # If a Celery broker/worker is available, enqueue background ingestion
        settings = get_settings()
        if settings.celery_broker_url or settings.redis_url:
            from backend.tasks import ingest_pair_task

            task = ingest_pair_task.delay(request.youtube_url, request.instagram_url)
            return {"job_id": task.id, "status": "queued"}

        # otherwise run synchronously
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
        # Always stream responses (SSE). Use vector retrieval for evidence.
        settings = get_settings()
        # Run the retrieval/build phases to get context and citations (no LLM yet)
        from backend.graph.workflow import retrieve_context

        graph_result = retrieve_context(request.question, request.thread_id, request.video_ids)

        # Persist the user's message immediately
        session.add(ChatHistory(thread_id=request.thread_id, role="user", content=request.question))
        session.commit()

        # If the client requested a non-streaming response, use the existing
        # run_workflow path to preserve backward compatibility (tests and
        # non-stream clients). Otherwise proceed with SSE streaming below.
        if not request.stream:
            result = run_workflow(request.question, request.thread_id, request.video_ids)
            session.add(
                ChatHistory(
                    thread_id=request.thread_id,
                    role="assistant",
                    content=result.answer,
                    sources_json=json.dumps(result.citations),
                )
            )
            session.commit()
            return ChatResponse(answer=result.answer, citations=result.citations, thread_id=request.thread_id)

        # Prepare OpenAI streaming call
        openai.api_key = settings.openai_api_key

        # Build messages for the chat model using the existing prompt template
        system_msg = (
            "You are an expert creator-video analyst. Answer only with grounded claims from the supplied context. "
            "Always explain comparisons, mention engagement reasoning, and include citations using Source: Video Name | Chunk N. "
            "If the answer is not in the context, say that the available sources do not contain enough evidence."
        )
        user_msg = (
            f"Question: {request.question}\n\nConversation memory:\n{graph_result.context}\n\n"
            f"Context:\n{graph_result.context}\n\nProvide a concise, evidence-based answer with source citations."
        )

        messages = [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]

        def event_stream() -> Generator[str, None, None]:
            # First emit retrieved citations so client can show sources progressively
            try:
                citations = graph_result.citations
            except Exception:
                citations = []
            init_payload = {"type": "retrieved", "citations": citations}
            yield f"data: {json.dumps(init_payload)}\n\n"

            # Call OpenAI streaming endpoint and yield token deltas
            try:
                resp = openai.ChatCompletion.create(model=settings.openai_model, messages=messages, stream=True)
                full_text = ""
                for chunk in resp:
                    if "choices" not in chunk:
                        continue
                    for choice in chunk.get("choices", []):
                        delta = choice.get("delta", {})
                        content = delta.get("content")
                        if content:
                            full_text += content
                            part_payload = {"type": "partial", "text": content}
                            yield f"data: {json.dumps(part_payload)}\n\n"
                # final event with full answer and citations
                final_payload = {"type": "done", "answer": full_text, "citations": citations}
                # persist assistant message
                try:
                    session.add(
                        ChatHistory(
                            thread_id=request.thread_id,
                            role="assistant",
                            content=full_text,
                            sources_json=json.dumps(citations),
                        )
                    )
                    session.commit()
                except Exception:
                    session.rollback()
                yield f"data: {json.dumps(final_payload)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as exc:
                err_payload = {"type": "error", "error": str(exc)}
                yield f"data: {json.dumps(err_payload)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})
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


@app.get("/ingest/status/{job_id}")
def ingest_status(job_id: str):
    """Check Celery job status for a background ingestion task."""
    from backend.celery_app import celery_app

    async_result = celery_app.AsyncResult(job_id)
    result = {
        "id": job_id,
        "state": async_result.state,
        "status": async_result.info if async_result else None,
    }
    return result


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
