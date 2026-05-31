Creator Video RAG Platform — Production Guide

This document covers production deployment, environment variables, performance testing, and scaling recommendations.

Quick start (Docker Compose production stack)
1. Create an `.env` file with required variables (see Environment Variables section).
2. Build and start services:

   docker-compose -f docker-compose.prod.yml up -d --build

3. Run DB migrations / init (recommended):
   - Exec into the backend container and run alembic or call the built-in init_db function.

Environment Variables
- OPENAI_API_KEY: (required) OpenAI API key for embeddings & LLM
- DATABASE_URL: (required) PostgreSQL connection string for production
- REDIS_URL / CELERY_BROKER_URL: (required) Redis URL for Celery broker and backend
- USE_QDRANT: true|false (optional) if true, backend will try to use Qdrant
- QDRANT_URL: if USE_QDRANT=true, the Qdrant API URL (e.g., http://qdrant:6333)
- QDRANT_API_KEY: (optional) Qdrant API key if protected
- ADMIN_SECRET: (optional) secret to protect admin endpoints

Deployment commands (examples)
- Docker Compose (production):
  docker-compose -f docker-compose.prod.yml up -d --build

- Kubernetes: build images and deploy with standard manifests; ensure services: backend, worker, redis, qdrant, postgres, frontend

Architecture diagram
```mermaid
flowchart LR
  subgraph Frontend
    F[Next.js frontend] -->|POST /ingest, POST /chat (SSE)| Backend
  end
  subgraph Backend
    Backend[FastAPI + LangGraph]
    Backend --> VectorDB[Qdrant/Chroma]
    Backend --> DB[Postgres]
    Backend --> Redis
    Backend --> CeleryWorker[Celery Workers]
    CeleryWorker --> Transcription[Whisper/yt-dlp]
    CeleryWorker --> VectorDB
  end
  Frontend -->|SSE| Backend
  VectorDB -->|kNN| Backend
  DB -->|metadata| Backend
```

Performance testing (k6)
- See `load_tests/` for k6 scripts. Run with:
  API_BASE=https://your-backend k6 run load_tests/k6_ingest.js

Scaling & cost-effectiveness for 1000 creators/day
- Ingestion is the heaviest path: transcription + chunking + embeddings are CPU/IO bound. Run ingestion in a separate worker pool with autoscaling.
- Vector DB (Qdrant) can be hosted as a managed service. One medium Qdrant node will handle retrievals at low cost.
- For 1000 creators/day (~1k ingests/day), average sustained ingestion rate ~= 0.0116 req/sec. Peak concurrency matters more — size worker pool for expected spikes, not daily average.
- Cost-effective setup:
  - 2–4 small worker nodes (2–4 vCPU) for ingestion (scale horizontally)
  - 1–2 app servers for fast API/streaming (uvicorn/gunicorn) (1–2 vCPU each)
  - 1 managed Redis + 1 managed Postgres
  - 1 Qdrant instance (managed or single VM)

This setup balances cost and capacity for 1000 creators/day with room to scale.

Performance report & optimization guidance
- Run k6 scenarios iteratively and capture p(95)/p(99) for ingest, retrieval, and streaming. Use the `Trend` metrics reported in k6 script outputs.
- If ingestion p(95) > 30s: increase worker CPU or parallelize transcription using faster models or GPU-backed whisper.
- If retrieval p(95) > 200ms: ensure Qdrant instance has sufficient RAM and correct vector indexing settings.
- If streaming TTFB is high: ensure API servers have enough workers and that the fronting load balancer supports SSE.

Contact
- For assistance with managed Qdrant or production scaling, request a consulting session.
