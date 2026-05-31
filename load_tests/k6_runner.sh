#!/usr/bin/env bash
# Helper to run k6 scripts with API_BASE env
API_BASE=${API_BASE:-http://localhost:8000}

echo "Running ingest test..."
API_BASE=${API_BASE} k6 run load_tests/k6_ingest.js

echo "Running retrieval test..."
API_BASE=${API_BASE} k6 run load_tests/k6_retrieval.js

echo "Running streaming test..."
API_BASE=${API_BASE} k6 run load_tests/k6_streaming.js
