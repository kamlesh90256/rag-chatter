Deployment guide — Vercel (frontend) and Railway (backend)

This document describes recommended steps and environment variables to deploy the project.

Vercel (Frontend)
------------------
1. Create a new project on Vercel and import the `frontend/` directory.
2. In Project Settings -> Environment Variables, add:
   - `NEXT_PUBLIC_API_BASE_URL` = https://<your-backend-url>
3. Build & Output Settings:
   - Framework Preset: Next.js
   - Build Command: `npm run build`
   - Output Directory: (Vercel will detect Next.js automatically)
4. Deploy and verify the static site. Use logs to debug build/runtime errors.

Railway (Backend)
------------------
1. Create a new Railway project and link the repository (or use the `backend/railway.json`).
2. Railway will detect `DOCKERFILE` build from `backend/Dockerfile` (see `backend/railway.json`).
3. Add environment variables in Railway (Production) matching `backend/.env.production.example`:
   - `OPENAI_API_KEY` (required)
   - `DATABASE_URL` (use managed Postgres in prod)
   - `CHROMA_PERSIST_DIR` (optional for local Chroma)
   - `CORS_ORIGINS` (set to your frontend origin)
   - `REDIS_URL` (if using Celery)
   - `RATE_LIMIT_PER_MINUTE`, `REQUEST_TIMEOUT_SECONDS`, `LOG_LEVEL`
4. Set the Railway start command (if not auto-detected):
   - `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
5. Deploy and monitor the Healthcheck path `/health`.

Secrets and Best Practices
--------------------------
- Never commit production secrets to the repo. Use the host's secret manager (Vercel Secrets, Railway Environment Variables).
- Use managed databases (Postgres) instead of SQLite in production.
- Pin base images by digest in CI or use the provided scheduled pinning workflow.
- Configure a secret rotation plan and revoke API keys when compromised.

CI/CD Recommendations
---------------------
- The repo includes a `cve-scan.yml` workflow that runs Trivy and comments on PRs with HIGH/CRITICAL findings.
- Use Dependabot to keep dependencies up-to-date (`.github/dependabot.yml` is configured).
- Optionally configure auto-deploy from `main` branch in Vercel and Railway. Use protected branches and required status checks.

Rollback & Migration
--------------------
- For schema migrations (when moving to Postgres), add migration tooling (Alembic or similar) and run migrations as a release step.

*** End Patch