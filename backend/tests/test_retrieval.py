from backend.rag.retrieval import RetrieverService


class FakeVectorStore:
    def __init__(self):
        self.calls = []

    def query(self, *, query_embedding, n_results=6, where=None):
        self.calls.append(
            {"query_embedding": query_embedding, "n_results": n_results, "where": where}
        )
        return [
            {
                "text": "chunk",
                "metadata": {"title": "Video A", "chunk_id": 1},
                "distance": 0.1,
            }
        ]


def test_retriever_uses_query_embedding(monkeypatch) -> None:
    monkeypatch.setattr("backend.rag.retrieval.embed_query", lambda text: [1.0, 2.0])
    service = RetrieverService()
    fake_store = FakeVectorStore()
    service.vectorstore = fake_store
    rows = service.retrieve("why did it work?", video_ids=["video-1"])
    assert rows[0]["metadata"]["title"] == "Video A"
    assert fake_store.calls[0]["query_embedding"] == [1.0, 2.0]
