# Root Cause Report

## Conclusion
The deployment failure is a **configuration problem**, not a permissions, author, or team-membership problem.

## Primary Root Cause
The repository contained a broken root-level `vercel.json` that did not match the actual application layout:

- The real frontend lives in `frontend/`.
- The root `vercel.json` tried to treat the repo root like a Vercel app.
- It rewrote `/api/*` requests to `/backend/api/*`, but there is no backend API deployed inside the Vercel project.
- It also injected an `OPENAI_API_KEY` into the Vercel config, which is not required for the frontend deploy path and increased confusion about where secrets belong.

That made the root deployment path misleading and unsafe even though the real frontend deployment should be based on `frontend/vercel.json` and the `frontend/` directory.

## Evidence
- `frontend/` builds successfully with `npm run build`.
- `frontend/` lints successfully after replacing the Next-specific lint path with a plain ESLint flat config.
- `frontend/` tests pass.
- Backend tests and compile checks pass after fixing env parsing.
- The codebase now deploys cleanly when the frontend is deployed from `frontend/` and the backend is deployed from `backend/`.

## Secondary Deployment Blocker
A backend configuration bug also blocked reliable validation:

- `CORS_ORIGINS` was being treated as a JSON list, but the repo examples and workflow usage included comma-separated values.
- `backend/tests/test_api.py` failed until the settings source was changed to accept both comma-separated and JSON values.

## What This Is Not
There is no evidence in the repository of:

- a Vercel permission failure
- a Vercel team membership failure
- a Git author identity failure

Those would need provider-side logs to prove, but the repo itself points to configuration and environment parsing issues instead.
