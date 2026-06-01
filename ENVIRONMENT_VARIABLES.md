# Environment Variables

## Frontend
Set in Vercel for `frontend/`:

- `NEXT_PUBLIC_API_BASE_URL` - Public backend API URL, for example `https://api.example.com`

## Backend
Set in Railway for `backend/`:

- `OPENAI_API_KEY` - OpenAI key for embeddings, chat, and transcription fallback
- `DATABASE_URL` - Production database connection string, preferably Railway Postgres
- `CHROMA_PERSIST_DIR` - Local Chroma persistence path when using local storage
- `CORS_ORIGINS` - Allowed frontend origins; accepts comma-separated values or JSON list values
- `RATE_LIMIT_PER_MINUTE` - API rate limit
- `REQUEST_TIMEOUT_SECONDS` - Request timeout in seconds
- `LOG_LEVEL` - Logging level
- `QDRANT_URL` - Qdrant endpoint when using managed Qdrant
- `QDRANT_API_KEY` - Qdrant API key when required
- `REDIS_URL` - Redis connection string for Celery and background work
- `CELERY_BROKER_URL` - Celery broker URL, usually the same as `REDIS_URL`
- `ADMIN_SECRET` - Secret for admin endpoints
- `USE_QDRANT` - Optional toggle if the deployment is switched to Qdrant-backed retrieval

## Notes
- Do not set `OPENAI_API_KEY` on the frontend unless you have a separate runtime reason to do so; the browser app only needs `NEXT_PUBLIC_API_BASE_URL`.
- For local development, the repo examples use `http://localhost:3000` for CORS and `http://localhost:8000` for the API base.
- If `CORS_ORIGINS` is set as a JSON list, the backend will accept that as well.
