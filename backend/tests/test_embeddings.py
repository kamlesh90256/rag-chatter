from backend.ingest import embeddings


class FakeEmbeddingsClient:
    def embed_documents(self, texts):
        return [[float(len(text))] for text in texts]

    def embed_query(self, text):
        return [float(len(text))]


def test_embed_texts_and_query(monkeypatch) -> None:
    monkeypatch.setattr(
        embeddings, "get_embeddings_client", lambda: FakeEmbeddingsClient()
    )
    assert embeddings.embed_texts(["hello", "world"]) == [[5.0], [5.0]]
    assert embeddings.embed_query("hello") == [5.0]
