# Backend

This directory contains the FastAPI backend for the Creator Video Intelligence RAG Platform.

Quick start (local, development)

1. Create and activate a virtual environment (PowerShell):

```powershell
python -m venv .venv-backend
.\.venv-backend\Scripts\Activate
```

2. Install the backend package in editable mode and dev tools:

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install -e .\backend
pip install ruff black isort pytest
```

3. Start the backend (use the provided helper to avoid accidental duplicate starts):

```powershell
# from repo root
.\scripts\start_backend.ps1
```

4. Check health:

```powershell
curl http://127.0.0.1:8000/health
```

Docker / Compose

The repository includes a `docker-compose.yml` to run the backend, frontend, Redis, and worker. Use `docker compose up --build` from the repo root. If you encounter port conflicts locally, stop the local backend and then bring up the compose stack.

Tests & linting

Run tests with `pytest` and fix lint issues with `ruff` / `black` / `isort`.

Notes

- The ingestion pipeline uses `yt-dlp` + OpenAI Whisper fallback for transcript extraction.
- You must set `OPENAI_API_KEY` in the environment for embeddings and Whisper fallback.
- On Windows, the backend will use a bundled `ffmpeg` binary from `imageio-ffmpeg` when a system `ffmpeg` install is missing.
- You can override the binary location with `FFMPEG_LOCATION` if needed.
- Persistent data (SQLite and Chroma) is stored under `./data/` by default.

If you run into issues starting the app, see `scripts/stop_backend.ps1` to kill any process holding port 8000.
