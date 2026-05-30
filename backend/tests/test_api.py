from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_endpoint(monkeypatch) -> None:
    sample = {
        "videos": [
            {"id": "a", "title": "Video A", "creator": "Creator A"},
            {"id": "b", "title": "Video B", "creator": "Creator B"},
        ],
        "comparison": {"engagement_rate": 12.5, "winner": "Video A", "table": []},
        "hook_analysis": {"video_a": {}, "video_b": {}},
        "analysis_id": "analysis-1",
    }
    monkeypatch.setattr(
        "backend.api.main.IngestionService.ingest_pair",
        lambda self, youtube_url, instagram_url: sample,
    )
    response = client.post(
        "/ingest",
        json={
            "youtube_url": "https://www.youtube.com/watch?v=abc",
            "instagram_url": "https://www.instagram.com/reel/xyz/",
        },
    )
    assert response.status_code == 200
    assert response.json()["analysis_id"] == "analysis-1"


def test_chat_endpoint(monkeypatch) -> None:
    class FakeResult:
        answer = "Grounded answer"
        citations = [
            {
                "title": "Video A",
                "creator": "Creator A",
                "chunk_id": 1,
                "url": "https://example.com",
            }
        ]

    monkeypatch.setattr(
        "backend.api.main.run_workflow",
        lambda question, thread_id, video_ids=None: FakeResult(),
    )
    response = client.post(
        "/chat",
        json={"question": "Compare them", "thread_id": "thread-1", "stream": False},
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "Grounded answer"


def test_sources_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.vectorstore.chroma.ChromaRepository.all_sources",
        lambda self, video_ids=None: [
            {"text": "chunk text", "metadata": {"title": "Video A", "chunk_id": 1}}
        ],
    )
    response = client.get(
        "/sources", params={"video_ids": "a,b", "thread_id": "thread-1"}
    )
    assert response.status_code == 200
    assert response.json()["sources"][0]["metadata"]["title"] == "Video A"
