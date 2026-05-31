# Loom Demo Checklist
Use this checklist when recording your Loom demo to make sure the demo flows smoothly.

- [ ] Intro: 30s overview of product and demo goals.
- [ ] Show architecture diagram (briefly explain components).
- [ ] Show Vercel frontend URL and quick navigation of UI.
- [ ] Trigger ingestion: paste a YouTube URL and run ingest.
- [ ] Show ingestion status and logs (worker output or admin endpoint).
- [ ] Open metadata page to show ingested video details.
- [ ] Demonstrate transcript extraction and chunking (show timestamps).
- [ ] Show embeddings generation and vectorstore count (admin or API).
- [ ] Ask a chat question that retrieves evidence and show citations with timestamps.
- [ ] Demonstrate streaming response (SSE) if available.
- [ ] Demonstrate memory across chat turns (ask follow-up question).
- [ ] Show analytics page and explain metrics.
- [ ] Show Docker / Railway dashboard with running services and logs.
- [ ] Wrap-up: mention remaining TODOs, where env/secrets live.
