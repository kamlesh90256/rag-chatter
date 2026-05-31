# Deployment Pipeline

This document describes the recommended deployment pipeline and the artifacts produced by CI.

Pipeline overview

1. Backend CI (push/pull_request)
   - Run unit and integration tests via `pytest`.
   - Compile checks (`python -m compileall`).
   - Build backend Docker image and push to GHCR as `rag-backend:latest` and a commit-tagged image.

2. Frontend CI (push/pull_request)
   - Run `npm ci`, `npm test` (if tests exist), and `npm run build`.
   - Upload the built `.next` artifact for downstream deployment jobs.

3. Smoke Test (manual or on push)
   - Start the backend in the runner and verify HTTP endpoints.
   - Run a lightweight ingest validation to confirm the ingestion endpoint responds.

Deployment recommendations
- Use a deployment job (CD) in a separate workflow that is triggered after `backend-ci` success. The job should pull the image from GHCR and deploy it to your chosen platform (Railway, AWS ECS, DigitalOcean App Platform, etc.).
- For the frontend, use Vercel (recommended for Next.js) or build a Docker image from the `frontend/Dockerfile` and deploy using the same image registry.

Required secrets and environment variables (summary)
- `GHCR_PAT` — write access to GitHub Container Registry.
- `OPENAI_API_KEY` — OpenAI API key for transcripts and embeddings.
- `DATABASE_URL` — Postgres or other DB connection string.
- `REDIS_URL` / `CELERY_BROKER_URL` — for Celery workers.
- `NEXT_PUBLIC_API_BASE_URL` — set in frontend deployment to point at production backend.

Status checks
- Protect `main` and require the backend and frontend CI workflows to pass before merging.

Next steps you can take
- Add a CD workflow that triggers on `workflow_run` success for `Backend CI` to deploy automatically.
- Provision secrets in GitHub repository Settings → Secrets → Actions.
