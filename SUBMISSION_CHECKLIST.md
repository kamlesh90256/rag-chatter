# Submission Checklist
Before submitting the project, verify the following items:

- [ ] All backend tests pass (`cd backend && pytest -q`).
- [ ] Frontend unit tests pass and build succeeds (`cd frontend && npm run test && npm run build`).
- [ ] Docker build succeeds locally (`docker build -f backend/Dockerfile -t rag-backend:local backend`).
- [ ] CI workflows are configured in GitHub actions.
- [ ] Vercel frontend is deployed and `NEXT_PUBLIC_API_BASE_URL` set correctly.
- [ ] Railway backend is deployed with Redis and Postgres configured.
- [ ] Celery worker is running and processing ingestion jobs.
- [ ] Example ingestion (YouTube) completes end-to-end.
- [ ] Retrieval returns citations with timestamps for a sample question.
- [ ] SSE streaming works for the chat endpoint.
- [ ] Architecture diagram added to repository.
- [ ] DEPLOYMENT.md, LOOM_DEMO_CHECKLIST.md, SUBMISSION_CHECKLIST.md present.
