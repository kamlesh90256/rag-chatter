```mermaid
flowchart LR
  subgraph CI
    A[GitHub Repo] --> B(Backend CI)
    A --> C(Frontend CI)
    B --> D[GHCR (images)]
    C --> E[Frontend build artifact]
  end

  subgraph CD
    D --> F[Vercel (frontend deploy)]
    D --> G[Railway (backend deploy)]
  end

  F --> H[Frontend Users]
  G --> I[API Clients]

  H -->|calls| G
  I -->|reads/writes| G

  subgraph Monitoring
    G --> M[Backend /metrics]
    F --> N[Frontend monitoring]
  end
```
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
