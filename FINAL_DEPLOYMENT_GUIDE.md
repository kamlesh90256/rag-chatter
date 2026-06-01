# Final Deployment Guide

## Minimal Architecture
- Frontend: Vercel
- Backend: Railway
- Database: Railway Postgres
- Vector DB: Qdrant
- Queue: Redis
- Worker: Railway worker using the backend image

## Deployment Order
1. Deploy the backend service on Railway from `backend/`.
2. Provision Railway Postgres and Redis.
3. Set backend environment variables on Railway.
4. Deploy the frontend from `frontend/` on Vercel.
5. Set `NEXT_PUBLIC_API_BASE_URL` in Vercel to the public Railway backend URL.
6. Add the frontend origin to `CORS_ORIGINS` on the backend.

## Backend Steps
- Build with the Dockerfile in `backend/Dockerfile`.
- Start with `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`.
- Run the worker with `celery -A backend.celery_app worker --loglevel=info -Q default`.

## Frontend Steps
- Use `frontend/vercel.json` and the `frontend/` directory.
- Build with `npm run build`.
- Keep runtime API access pointed at the Railway backend URL through `NEXT_PUBLIC_API_BASE_URL`.

## Validation Checklist
- Frontend build passes.
- Frontend lint passes.
- Frontend tests pass.
- Backend tests pass.
- Backend compile checks pass.
- Vercel project points at `frontend/`, not the repo root.
- Railway secrets match the documented names.

## Deployment Notes
- The repo no longer relies on the broken root-level Vercel config.
- Backend CORS parsing now accepts the repo examples and production env styles.
- If you use managed Qdrant, set `QDRANT_URL` and `QDRANT_API_KEY`; otherwise leave Qdrant disabled and use the local Chroma path.
