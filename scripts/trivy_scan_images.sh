#!/usr/bin/env bash
set -euo pipefail

if ! command -v trivy >/dev/null 2>&1; then
  echo "trivy not found. Install Trivy: https://aquasecurity.github.io/trivy/installation/"
  exit 2
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found. Install Docker Desktop or Docker Engine to build images."
  exit 2
fi

BACKEND_TAG=rag-chatter-backend:local
FRONTEND_TAG=rag-chatter-frontend:local

echo "Building backend image..."
docker build -t "$BACKEND_TAG" ./backend

echo "Scanning backend image (HIGH+CRITICAL)..."
trivy image --severity HIGH,CRITICAL --exit-code 1 --format table "$BACKEND_TAG" || {
  echo "Trivy detected HIGH/CRITICAL vulnerabilities in backend image." >&2
  exit 1
}

echo "Building frontend image..."
docker build -t "$FRONTEND_TAG" ./frontend

echo "Scanning frontend image (HIGH+CRITICAL)..."
trivy image --severity HIGH,CRITICAL --exit-code 1 --format table "$FRONTEND_TAG" || {
  echo "Trivy detected HIGH/CRITICAL vulnerabilities in frontend image." >&2
  exit 1
}

echo "No HIGH/CRITICAL vulnerabilities found in built images."
