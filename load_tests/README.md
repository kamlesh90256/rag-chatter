k6 Load Test Suite

This folder contains k6 scripts to simulate load for ingestion, retrieval, and streaming.

Prerequisites
- Install k6 (https://k6.io/docs/getting-started/installation)
- Ensure the backend is running and reachable via `API_BASE` environment variable or default `http://localhost:8000`.

Scripts
- k6_ingest.js — simulates ingestion POST /ingest traffic.
- k6_retrieval.js — simulates non-streaming chat retrieval POST /chat (stream=false).
- k6_streaming.js — simulates streaming POST /chat (stream=true) and records TTFB and full duration.

Running
- Run ingest scenario (example):

  API_BASE=http://localhost:8000 k6 run load_tests/k6_ingest.js

- Run retrieval scenario:

  API_BASE=http://localhost:8000 k6 run load_tests/k6_retrieval.js

- Run streaming scenario:

  API_BASE=http://localhost:8000 k6 run load_tests/k6_streaming.js

Simulating creators/day
- "Creators/day" is a business metric. To map to k6 VUs:
  - 100 creators/day -> ~0.00116 req/sec per creator (spread over 24h)
  - For load testing, focus on peak concurrency. Example traffic profiles:
    - 100 creators/day: test with 10-20 concurrent users for short bursts
    - 500 creators/day: test with 50-100 concurrent users
    - 1000 creators/day: test with 100-200 concurrent users

Metrics captured
- ingestion_latency_ms (ingest)
- retrieval_latency_ms (non-stream retrieval)
- streaming_ttfb_ms (time to first byte for SSE)
- streaming_full_ms (time to full response)

Interpreting results
- Use k6 summary output to inspect p(50), p(90), p(95), and p(99) for the trends reported.
- Focus on p(95) thresholds for SLO compliance.

Notes
- Ingestion tasks are CPU and I/O heavy (transcoding, transcription, embedding). For production load, use Celery workers with autoscaling and separate the ingestion worker pool from real-time retrieval workers.
