# CI Setup

This document lists how to enable CI and required secrets for the GitHub Actions workflows added to this repository.

Workflows added:
- `.github/workflows/backend-ci.yml` — runs backend tests, compile checks, builds Docker image and pushes to GitHub Container Registry (GHCR).
- `.github/workflows/frontend-ci.yml` — installs frontend dependencies, runs tests (if present), builds the Next.js app and uploads build artifact.
- `.github/workflows/smoke-test.yml` — starts the backend and validates basic endpoints (`/health`, `/metadata`, `/sources`) and performs a lightweight ingestion request.

Required repository secrets
- `GHCR_PAT`: Personal Access Token with `write:packages` scope for pushing to `ghcr.io`. Alternatively configure fine-grained packages permissions.
- `OPENAI_API_KEY`: Required by runtime tests if the ingestion/transcript/embeddings steps are enabled.
- `DATABASE_URL`: Production database connection string used by backend (if applicable in CI). For CI jobs that require DB integration, set to a test DB.
- `REDIS_URL`: If smoke tests or integration tests require Celery/Redis, configure a Redis service and set this secret.

Recommended branch protection / status checks
- Require status checks for `main` branch: `Backend CI / build-and-push`, `Backend CI / test`, `Frontend CI / build` and `Smoke Test / smoke`.
- Enable "Require branches to be up to date before merging" to ensure CI runs on the exact merge commit.

Notes
- The `backend-ci` workflow logs into GHCR using `GHCR_PAT`. You can also use the repository's `GITHUB_TOKEN` in many cases, but `GITHUB_TOKEN` may not have package write permission depending on org settings.
- The smoke test runs a lightweight HTTP verification only — it avoids expensive live API calls. If you want a full end-to-end ingest test that requires OpenAI or YouTube credentials, add a CI job that references the `OPENAI_API_KEY` and `YOUTUBE_API_KEY` secrets.
