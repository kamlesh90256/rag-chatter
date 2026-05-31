# Final Deployment Checklist

Before running the Continuous Deployment workflow, ensure the following items are complete.

1. Repository secrets (GitHub Settings → Secrets → Actions):
   - GHCR_PAT
   - VERCEL_TOKEN
   - VERCEL_ORG_ID
   - VERCEL_PROJECT_ID
   - RAILWAY_API_KEY
   - RAILWAY_PROJECT_ID
   - RAILWAY_SERVICE_ID
   - FRONTEND_URL
   - BACKEND_URL

2. CI workflows passing on `main`:
   - Backend CI (tests + build and push)
   - Frontend CI (install + build)
   - Smoke Test (optional but recommended)

3. Branch protection for `main` enabled and checks required.

4. Vercel project configured and environment variables set (frontend):
   - NEXT_PUBLIC_API_BASE_URL, OPENAI_API_KEY (optional), CORS_ORIGINS

5. Railway project configured and environment variables set (backend):
   - OPENAI_API_KEY, DATABASE_URL, REDIS_URL, CELERY_BROKER_URL, ADMIN_SECRET, QDRANT_* (if used)

6. Verify builds locally (recommended):
   - Frontend: `cd frontend && npm ci && npm run build` (ensure `.next` produced)
   - Backend: `python -m compileall backend` (no syntax errors)

7. Docker availability (optional local deploy):
   - Docker CLI installed if you plan to `docker build` locally. If Docker is unavailable locally, CI `backend-ci` will build/push images to GHCR.

8. Run the CD workflow (it triggers automatically after CI success) or manually from Actions UI.

9. After deployment, validate:
   - `FRONTEND_URL` responds (HTTP 200 on landing page)
   - `BACKEND_URL/health` returns HTTP 200
   - `/metadata` and `/sources` endpoints respond as expected
