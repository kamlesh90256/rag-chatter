Performance Report Template

Run Summary
- Date:
- Environment: (local/docker/production)
- API_BASE:
- Test duration per script:

Test Scenarios
- Ingest load (k6_ingest.js): VUs / duration / stages
- Retrieval load (k6_retrieval.js): VUs / duration
- Streaming load (k6_streaming.js): VUs / duration

Key Metrics (collect from k6 summary)
- ingestion_latency_ms p(50) / p(90) / p(95) / p(99)
- retrieval_latency_ms p(50) / p(90) / p(95) / p(99)
- streaming_ttfb_ms p(50) / p(90) / p(95) / p(99)
- streaming_full_ms p(50) / p(90) / p(95) / p(99)
- http_req_failed rate

Observations
- Bottlenecks observed (CPU, memory, I/O, network)
- Failed requests and error types

Recommendations
- Increase Celery worker count or CPU for ingestion
- Move transcription to GPU-backed nodes or faster models
- Use managed Qdrant or increase Qdrant memory
- Cache frequently used embeddings and results

Appendix
- Raw k6 outputs (attach)
- Docker Compose resource usage (docker stats)
