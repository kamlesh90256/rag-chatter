# Deployment Fixes

## Frontend
- Removed the broken root-level `vercel.json`.
- Kept the real Vercel config in `frontend/vercel.json` as the authoritative frontend deploy config.
- Replaced the Next-specific lint path with a plain ESLint flat config.
- Added ESLint/TypeScript flat-config dependencies needed for `npm run lint` to work.
- Narrowed lint coverage to app code instead of generated/config files.

## Backend
- Fixed duplicate settings declarations in `backend/utils/settings.py`.
- Made `CORS_ORIGINS` parsing tolerant of both comma-separated and JSON inputs.
- Restored the missing `json` import in `backend/api/main.py`.
- Removed duplicate dependencies from `backend/pyproject.toml`.

## GitHub Actions
- Standardized Railway secret usage in deploy workflows.
- Replaced the inconsistent `RAILWAY_TOKEN` path with `RAILWAY_API_KEY` in the backend Railway deploy job.
- Removed the silent success path from the combined deployment workflow so Railway failures are visible.

## Result
The repository now has a clean frontend deploy path for Vercel and a cleaner backend deploy path for Railway with the documented secret names and runtime behavior aligned to the repo examples.
