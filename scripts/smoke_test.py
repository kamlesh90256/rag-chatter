from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from sqlmodel import Session

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.graph.workflow import get_graph, run_workflow
from backend.ingest.analysis import build_comparison_table, calculate_engagement_rate
from backend.ingest.pipeline import IngestionService
from backend.rag.retrieval import RetrieverService
from backend.utils.database import engine
from backend.vectorstore.chroma import ChromaRepository


@dataclass
class CheckResult:
    name: str
    passed: bool
    evidence: str


def _short(value: Any, limit: int = 220) -> str:
    text = json.dumps(value, ensure_ascii=False, default=str) if isinstance(value, (dict, list)) else str(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _record(results: dict[str, CheckResult], name: str, passed: bool, evidence: str) -> None:
    existing = results.get(name)
    if existing is None:
        results[name] = CheckResult(name=name, passed=passed, evidence=evidence)
        return
    existing.passed = existing.passed and passed
    existing.evidence = f"{existing.evidence}; {evidence}"


def _health_check(client: httpx.Client, results: dict[str, CheckResult], base_url: str) -> None:
    try:
        response = client.get(f"{base_url}/health")
        payload = response.json()
        _record(results, "Backend health", response.status_code == 200 and payload.get("status") == "ok", _short(payload))
    except Exception as exc:
        _record(results, "Backend health", False, str(exc))


def _stream_chat(client: httpx.Client, base_url: str, thread_id: str, video_ids: list[str], question: str) -> dict[str, Any]:
    payload = {"question": question, "thread_id": thread_id, "video_ids": video_ids, "stream": True}
    answer = ""
    citations: list[dict[str, Any]] = []
    got_done = False
    with client.stream("POST", f"{base_url}/chat", json=payload, headers={"Accept": "text/event-stream"}) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            data = line[6:].strip()
            if data == "[DONE]":
                got_done = True
                break
            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                continue
            answer = event.get("answer", answer)
            citations = event.get("citations", citations)
    return {"answer": answer, "citations": citations, "done": got_done}


def main() -> int:
    base_url = os.getenv("SMOKE_BACKEND_URL", "http://127.0.0.1:8000")
    youtube_url = os.getenv("SMOKE_YOUTUBE_URL", "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    instagram_url = os.getenv(
        "SMOKE_INSTAGRAM_URL",
        "https://www.instagram.com/reel/DY3lF6xSmqc/?igsh=MnZtajhyNzZoY2w4",
    )
    thread_id = f"smoke-{uuid.uuid4()}"
    question = "Compare the two videos and explain which one should perform better."
    follow_up = "What did we already learn from those videos?"
    results: dict[str, CheckResult] = {}

    with httpx.Client(timeout=1200.0) as client:
        _health_check(client, results, base_url)

        with Session(engine) as session:
            service = IngestionService(session)
            try:
                youtube = service.ingest_single(youtube_url)
                yt_video = youtube["video"]
                yt_transcript = youtube["transcript"]
                yt_chunks = youtube["chunks"]
                _record(results, "YouTube ingestion", bool(yt_video.id and yt_video.platform == "youtube"), _short({"id": yt_video.id, "title": yt_video.title, "url": yt_video.url}))
                _record(results, "Metadata extraction", bool(yt_video.title and yt_video.creator), f"youtube={_short({'title': yt_video.title, 'creator': yt_video.creator, 'views': yt_video.views})}")
                _record(results, "Transcript extraction", bool(yt_transcript.text), f"youtube={_short({'source_type': yt_transcript.source_type, 'chars': len(yt_transcript.text)})}")
                _record(results, "ChromaDB insertion", len(yt_chunks) > 0, f"youtube={_short({'chunks': len(yt_chunks), 'first_chunk': yt_chunks[0].text[:120] if yt_chunks else ''})}")
            except Exception as exc:
                _record(results, "YouTube ingestion", False, str(exc))
                _record(results, "Metadata extraction", False, f"youtube={exc}")
                _record(results, "Transcript extraction", False, f"youtube={exc}")
                _record(results, "ChromaDB insertion", False, f"youtube={exc}")
                youtube = None

            try:
                instagram = service.ingest_single(instagram_url)
                ig_video = instagram["video"]
                ig_transcript = instagram["transcript"]
                ig_chunks = instagram["chunks"]
                _record(results, "Instagram ingestion", bool(ig_video.id and ig_video.platform == "instagram"), _short({"id": ig_video.id, "title": ig_video.title, "url": ig_video.url}))
                _record(results, "Metadata extraction", bool(ig_video.title and ig_video.creator), f"instagram={_short({'title': ig_video.title, 'creator': ig_video.creator, 'views': ig_video.views})}")
                _record(results, "Transcript extraction", bool(ig_transcript.text), f"instagram={_short({'source_type': ig_transcript.source_type, 'chars': len(ig_transcript.text)})}")
                _record(results, "ChromaDB insertion", len(ig_chunks) > 0, f"instagram={_short({'chunks': len(ig_chunks), 'first_chunk': ig_chunks[0].text[:120] if ig_chunks else ''})}")
            except Exception as exc:
                _record(results, "Instagram ingestion", False, str(exc))
                _record(results, "Metadata extraction", False, f"instagram={exc}")
                _record(results, "Transcript extraction", False, f"instagram={exc}")
                _record(results, "ChromaDB insertion", False, f"instagram={exc}")
                instagram = None

            if youtube and instagram:
                comparison = build_comparison_table(youtube["video"].model_dump(), instagram["video"].model_dump())
                yt_rate = calculate_engagement_rate(youtube["video"].likes, youtube["video"].comments, youtube["video"].views)
                ig_rate = calculate_engagement_rate(instagram["video"].likes, instagram["video"].comments, instagram["video"].views)
                expected_winner = youtube["video"].title if yt_rate >= ig_rate else instagram["video"].title
                _record(results, "Engagement calculation", comparison.winner == expected_winner and comparison.engagement_rate == max(yt_rate, ig_rate), _short({"youtube_rate": yt_rate, "instagram_rate": ig_rate, "winner": comparison.winner}))
            else:
                _record(results, "Engagement calculation", False, "Missing ingested videos")

            video_ids = []
            if youtube:
                video_ids.append(youtube["video"].id)
            if instagram:
                video_ids.append(instagram["video"].id)

            try:
                retriever = RetrieverService()
                retrieved = retriever.retrieve(
                    "Which video has the stronger hook?", video_ids=video_ids or None
                )
                _record(
                    results,
                    "Retrieval",
                    len(retrieved) > 0,
                    _short({"results": len(retrieved), "top": retrieved[0] if retrieved else {}}),
                )
            except Exception as exc:
                _record(results, "Retrieval", False, str(exc))

            try:
                first = run_workflow(question, thread_id, video_ids or None)
                second = run_workflow(follow_up, thread_id, video_ids or None)
                graph = get_graph()
                snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
                memory_ok = bool(snapshot and getattr(snapshot, "values", None) is not None)
                if memory_ok:
                    memory_ok = bool(snapshot.values.get("answer")) and bool(snapshot.values.get("question"))
                _record(
                    results,
                    "LangGraph memory",
                    memory_ok and bool(first.answer) and bool(second.answer),
                    _short(
                        {
                            "first_answer": first.answer[:120],
                            "second_answer": second.answer[:120],
                            "snapshot_has_state": bool(snapshot),
                        }
                    ),
                )
            except Exception as exc:
                _record(results, "LangGraph memory", False, str(exc))

            try:
                chat = _stream_chat(client, base_url, thread_id, video_ids, question)
                citations = chat.get("citations") or []
                _record(
                    results,
                    "Streaming responses",
                    bool(chat.get("done")) and bool(chat.get("answer")),
                    _short({"done": chat.get("done"), "answer": chat.get("answer", "")[:120]}),
                )
                _record(
                    results,
                    "Citations",
                    bool(citations) and all(isinstance(item, dict) and item.get("url") for item in citations),
                    _short(citations[:2]),
                )
            except Exception as exc:
                _record(results, "Streaming responses", False, str(exc))
                _record(results, "Citations", False, str(exc))

    ordered_names = [
        "Backend health",
        "YouTube ingestion",
        "Instagram ingestion",
        "Metadata extraction",
        "Transcript extraction",
        "Engagement calculation",
        "ChromaDB insertion",
        "Retrieval",
        "LangGraph memory",
        "Streaming responses",
        "Citations",
    ]
    report_lines = ["# Smoke Test Report", ""]
    for name in ordered_names:
        item = results.get(name)
        if item is None:
            continue
        status = "PASS" if item.passed else "FAIL"
        report_lines.append(f"- **{item.name}**: {status} — {item.evidence}")

    report_path = ROOT / "SMOKE_TEST_REPORT.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    for name in ordered_names:
        item = results.get(name)
        if item is None:
            continue
        print(f"{item.name}: {'PASS' if item.passed else 'FAIL'}")

    return 0 if all(item.passed for item in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())