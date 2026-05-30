# Scaling Plan for 1000 Creators/Day

This platform can reach a practical 1000 creators/day with a staged architecture.

## Current Baseline

- FastAPI handles ingest and question answering.
- ChromaDB stores chunks and supports retrieval.
- LangGraph MemorySaver persists conversational context.
- SQLModel stores metadata, transcripts, chunks, chats, and analyses.

## Required Scaling Additions

### Redis Cache

Use Redis to cache:

- video metadata lookups
- repeat transcript fetch results
- repeated retrieval results for similar questions
- session-level conversation summaries

### Background Jobs

Move ingestion off the request path.

- HTTP request validates URLs and enqueues a job.
- Worker downloads metadata and transcripts.
- Worker chunks, embeds, and writes vectors.
- Worker computes comparison and hook analysis.
- UI polls job status or receives webhook/SSE updates.

### Celery or Equivalent Queue

A Celery worker cluster is a straightforward fit:

- broker: Redis
- result backend: Redis or Postgres
- task types: metadata extraction, transcript fetch, Whisper fallback, embedding batch writes

### Async Workers

Scale transcription and embedding jobs separately from API traffic.

- API pods stay responsive.
- Worker pods scale by queue depth.
- Long-running Whisper tasks do not block chat responses.

### Embedding Batching

Batch chunk embeddings per ingest job.

- fewer API round-trips
- lower per-item overhead
- easier retry handling

### Horizontal Scaling

Scale the FastAPI service horizontally.

- keep API nodes stateless
- move cache/session coordination into Redis/Postgres
- keep vector write operations idempotent

### Qdrant Migration

ChromaDB is a solid early-stage choice, but Qdrant becomes a good next step when:

- multi-node retrieval is needed
- stronger filtering and payload indexing are required
- persistent, managed vector search is preferred

Migration path:

1. Keep the chunk metadata schema stable.
2. Wrap vector-store operations behind a repository interface.
3. Replace Chroma with Qdrant behind the same interface.
4. Re-index existing chunks with the new store.

## Cost Optimization

- Use transcript-first ingestion to avoid Whisper whenever possible.
- Prefer chunk-level retrieval over large prompt windows.
- Cache comparison results for unchanged source URLs.
- Store only normalized metadata fields in relational storage.
- Use background jobs to avoid wasted retries from client timeouts.

## Operating Targets

A sensible target envelope for 1000 creators/day:

- Ingest jobs: worker-driven
- Chat latency: sub-5s for retrieval + GPT-4o-mini generation on typical prompts
- Storage: SQLite for local dev, Postgres for production metadata, object storage for artifacts, vector DB for chunks
- Reliability: retries with backoff, dead-letter queue, and idempotent job keys
