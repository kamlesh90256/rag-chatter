# Deployment Automation

This document describes the Continuous Deployment workflow and required secrets for automatic deployment to Vercel (frontend) and Railway (backend).

Files added
- `.github/workflows/deployment.yml` — triggers when `Backend CI` and `Frontend CI` complete successfully and performs automated deployments.

How it triggers
- The deployment workflow uses `workflow_run` to detect when the `Backend CI` and `Frontend CI` workflows complete. It verifies their latest run conclusions on `main` before proceeding.

Secrets required for deployment
- `VERCEL_TOKEN` — Vercel personal token with project deploy permission.
- `VERCEL_ORG_ID` — Vercel organization ID.
- `VERCEL_PROJECT_ID` — Vercel project ID for the frontend.
- `RAILWAY_API_KEY` — Railway API key with deploy permissions.
- `RAILWAY_PROJECT_ID` — Railway project id where backend service lives.
- `RAILWAY_SERVICE_ID` — Railway service id for the backend service to deploy.
- `FRONTEND_URL` — Public URL of the frontend (used for verification). Example: `https://your-app.vercel.app`.
- `BACKEND_URL` — Public base URL of the backend (used for verification). Example: `https://api.yourdomain.com`.

Notes about Railway deployment
- The workflow installs the Railway CLI and runs `railway up` against the configured project and service. Configure your Railway project with the necessary environment variables (e.g., `OPENAI_API_KEY`, `DATABASE_URL`, `REDIS_URL`, etc.) in Railway prior to automatic deploy.

Verification
- After deployments, the workflow attempts to hit `FRONTEND_URL` and `BACKEND_URL/health` up to 20 times, waiting for availability.

Security
- Store all tokens in GitHub Secrets (Settings → Secrets → Actions). Do not print secret values in workflow logs.
# Deployment Guide — Creator Video Intelligence RAG Platform

This document describes how to deploy the frontend to Vercel and the backend to Railway (recommended). It contains exact commands, CI workflows, environment variables and smoke-test checks to make the project demo-ready.

## Summary
- Frontend: Next.js app in `frontend/` — deploy to Vercel (recommended)
- Backend: FastAPI app in `backend/` — deploy to Railway using Docker or the Railway Git integration
- Worker: Celery worker (uses Redis)
- Vector store: Qdrant (managed) or Chroma (local persistence)

## Required environment variables
Set these in Vercel (frontend) and Railway (backend) environments.

- `OPENAI_API_KEY` — your OpenAI API key (optional for demo; some features degrade without it)
- `DATABASE_URL` — production database (Postgres recommended). Example: `postgresql://user:pass@host:5432/db`
- `REDIS_URL` — Redis connection string for Celery: `redis://<host>:6379/0`
- `CELERY_BROKER_URL` — usually same as `REDIS_URL`
- `QDRANT_URL` — if using a managed Qdrant instance (optional)
- `QDRANT_API_KEY` — Qdrant API key (if required)
- `CORS_ORIGINS` — frontend origins as a comma-separated list or JSON list, e.g. `https://your-frontend.vercel.app` or `['https://your-frontend.vercel.app']`
- `NEXT_PUBLIC_API_BASE_URL` — public URL for the backend API (frontend runtime)
- `ADMIN_SECRET` — secret for admin endpoints

## Frontend — Vercel

1. Push your repo to GitHub if it isn't already.
2. In Vercel, import the repository and select the `frontend` project folder.
3. Vercel build settings are already specified in `frontend/vercel.json`:
   - Build: `npm run build`
   - Install: `npm install`
   - Dev: `npm run dev`
4. Set Environment Variables in Vercel (see list above). Make sure `NEXT_PUBLIC_API_BASE_URL` points to the backend's public URL (e.g. `https://api.example.com`).
5. Deploy — Vercel will run `npm run build` automatically. You can also use the Vercel CLI:

```bash
cd frontend
npm i -g vercel
vercel login
vercel --prod
```

## Backend — Railway (Docker deploy)

Railway supports both direct GitHub integration and Docker deployments. We recommend using Railway's Git integration and pointing it at the `backend` folder, or pushing a Docker image to a registry and configuring Railway to use the image.

Option A — GitHub deploy (recommended):
1. In Railway, create a new project and connect your GitHub repository.
2. Configure the service to use the `backend` folder and the `Dockerfile` in `backend/` (Railway will detect and build the image).
3. Add environment variables in Railway (see list above).
4. Add Railway plugins for Redis and Postgres in the project (Railway has managed addons). Use their connection strings to populate `REDIS_URL` and `DATABASE_URL`.
5. Set a `SECRET` value for `ADMIN_SECRET`.

Option B — Docker image push + Railway image deploy:
1. Build and push the backend image to a registry (GHCR or Docker Hub):

```bash
# from repo root
docker build -f backend/Dockerfile -t ghcr.io/<your-org>/rag-backend:latest backend
docker push ghcr.io/<your-org>/rag-backend:latest
```

2. In Railway, create a new service and choose "Deploy from Image" and give the image URL. Configure environment variables and addons as above.

## Worker

- The `worker` service is defined in `docker-compose.yml` and uses the same Dockerfile to run `celery`.
- On Railway you can create a second service that runs the worker command:
  `celery -A backend.celery_app worker --loglevel=info -Q default`

## Docker Compose (for VM/self-host)

The repository includes `docker-compose.yml` for an opinionated local/VM deployment including backend, frontend (optional), redis and worker. To start locally on a machine with Docker:

```bash
# from repo root
docker compose up --build -d
# check backend
curl -sS http://localhost:8000/health
```

Note: Docker must be installed locally to run this.

## Verification smoke checks
After deployment, verify these endpoints (replace `API_BASE` with `NEXT_PUBLIC_API_BASE_URL`):

```bash
# health
curl -sS ${API_BASE}/health

# metadata
curl -sS ${API_BASE}/metadata

# sources
curl -sS "${API_BASE}/sources?thread_id=test-thread"

# ingest (POST)
curl -sS -X POST ${API_BASE}/ingest -H "Content-Type: application/json" -d '{"youtube_url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","instagram_url":null}'
```

## CI / GitHub Actions
- We include example GitHub Actions workflows in `.github/workflows/` to build & push backend images and optionally trigger deployments.

## Troubleshooting & Blockers
- You will need to provide API keys and credentials (OpenAI, Qdrant, Railway, Docker/registry credentials) in environment variables / Railway secrets.
- For Qdrant, either use a managed Qdrant instance (set `QDRANT_URL` and `QDRANT_API_KEY`) or use Chroma (local) by leaving Qdrant unset.

---
Generated by the project automation assistant.
