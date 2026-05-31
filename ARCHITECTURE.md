```mermaid
flowchart LR
  Browser[User Browser]
  Browser -->|HTTP| VercelFrontend[Frontend (Vercel) Next.js]
  VercelFrontend -->|REST / SSE| BackendAPI[Backend API (FastAPI) - Railway]
  BackendAPI --> DB[(Postgres)]
  BackendAPI --> Redis[(Redis)]
  BackendAPI --> Qdrant[(Qdrant)]
  BackendAPI -->|enqueue| CeleryWorker[Celery Worker]
  CeleryWorker --> Redis
  CeleryWorker --> Qdrant
  BackendAPI -->|vectorstore| Chroma[(Chroma Local) - optional]
  BackendAPI --> LangGraph[LangGraph]
```

Components:
- Frontend: Next.js app deployed to Vercel (static + client-side rendering)
- Backend: FastAPI app deployed to Railway (Dockerized)
- Worker: Celery worker for background ingestion and long-running tasks
- Redis: broker for Celery
- Qdrant or Chroma: Vector store for embeddings
- LangGraph: orchestration for workflows
