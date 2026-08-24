#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DOCKERFILE="$REPO_ROOT/backend/Dockerfile"
FRONTEND_DOCKERFILE="$REPO_ROOT/frontend/Dockerfile"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to run this script. Install Docker Desktop or Docker Engine."
  exit 2
fi

echo "Reading current ARG defaults from Dockerfiles..."
PYTHON_ARG_LINE=$(grep -E '^ARG[[:space:]]+PYTHON_BASE=' "$BACKEND_DOCKERFILE" || true)
NODE_ARG_LINE=$(grep -E '^ARG[[:space:]]+NODE_BASE=' "$FRONTEND_DOCKERFILE" || true)

if [ -z "$PYTHON_ARG_LINE" ] || [ -z "$NODE_ARG_LINE" ]; then
  echo "Could not find ARG PYTHON_BASE or ARG NODE_BASE in Dockerfiles."
  exit 3
fi

PYTHON_IMAGE=${PYTHON_ARG_LINE#*=}
NODE_IMAGE=${NODE_ARG_LINE#*=}

echo "Pulling $PYTHON_IMAGE..."
docker pull "$PYTHON_IMAGE"
PYTHON_DIGEST=$(docker image inspect --format='{{index .RepoDigests 0}}' "$PYTHON_IMAGE" 2>/dev/null || true)
if [ -z "$PYTHON_DIGEST" ]; then
  echo "Failed to resolve digest for $PYTHON_IMAGE"
  exit 4
fi

echo "Pulling $NODE_IMAGE..."
docker pull "$NODE_IMAGE"
NODE_DIGEST=$(docker image inspect --format='{{index .RepoDigests 0}}' "$NODE_IMAGE" 2>/dev/null || true)
if [ -z "$NODE_DIGEST" ]; then
  echo "Failed to resolve digest for $NODE_IMAGE"
  exit 4
fi

echo "Pinning backend Dockerfile ARG to $PYTHON_DIGEST"
cp "$BACKEND_DOCKERFILE" "$BACKEND_DOCKERFILE.bak"
sed -E -i "s|^ARG[[:space:]]+PYTHON_BASE=.*|ARG PYTHON_BASE=${PYTHON_DIGEST}|" "$BACKEND_DOCKERFILE"

echo "Pinning frontend Dockerfile ARG to $NODE_DIGEST"
cp "$FRONTEND_DOCKERFILE" "$FRONTEND_DOCKERFILE.bak"
sed -E -i "s|^ARG[[:space:]]+NODE_BASE=.*|ARG NODE_BASE=${NODE_DIGEST}|" "$FRONTEND_DOCKERFILE"

echo "Pinned Dockerfiles. Backups: ${BACKEND_DOCKERFILE}.bak, ${FRONTEND_DOCKERFILE}.bak"
echo "Inspect changes and commit them if satisfied."
