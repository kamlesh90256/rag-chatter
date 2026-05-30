ARG PYTHON_BASE=python:3.12.8-slim-bookworm
FROM ${PYTHON_BASE} AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ffmpeg; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY . .

# Upgrade pip and install package without cache to reduce image size
RUN pip install --upgrade pip setuptools wheel \
  && pip install --no-cache-dir .

# Expose celery CLI (installed via pyproject dependencies)
# The container image will have `celery` available on PATH after installation

# Create a non-root user and use it at runtime
RUN useradd --create-home --shell /bin/bash appuser \
  && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
