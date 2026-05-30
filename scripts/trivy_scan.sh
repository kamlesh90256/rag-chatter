#!/usr/bin/env bash
set -euo pipefail

if ! command -v trivy >/dev/null 2>&1; then
  echo "trivy not found. Install Trivy: https://aquasecurity.github.io/trivy/installation/"
  exit 2
fi

echo "Running Trivy filesystem scan (HIGH+CRITICAL)..."
trivy fs --severity HIGH,CRITICAL --exit-code 1 --format table . || {
  echo "Trivy found vulnerabilities (exit code non-zero). Review output above." >&2
  exit 1
}

echo "No HIGH/CRITICAL vulnerabilities found by Trivy (filesystem scan)."
