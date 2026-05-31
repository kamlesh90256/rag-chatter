from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import multiprocess
import time
from typing import Optional

registry = CollectorRegistry()

# HTTP request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"],
    registry=registry,
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency seconds",
    ["method", "endpoint"],
    registry=registry,
)

# Application-specific metrics
INGEST_DURATION = Histogram(
    "ingest_duration_seconds",
    "Duration of ingestion pipeline (seconds)",
    registry=registry,
)

RETRIEVAL_DURATION = Histogram(
    "retrieval_duration_seconds",
    "Duration of retrieval operations (seconds)",
    registry=registry,
)

STREAM_TTFB = Histogram(
    "streaming_ttfb_seconds",
    "Streaming time to first byte (seconds)",
    registry=registry,
)

STREAM_FULL = Histogram(
    "streaming_full_seconds",
    "Streaming full completion time (seconds)",
    registry=registry,
)

VECTOR_SEARCH = Histogram(
    "vector_search_seconds",
    "Vector search latency (seconds)",
    registry=registry,
)

EMBEDDING_DURATION = Histogram(
    "embedding_duration_seconds",
    "Embedding generation latency (seconds)",
    registry=registry,
)

ERROR_COUNT = Counter(
    "errors_total",
    "Total application errors",
    ["where"],
    registry=registry,
)

# Celery / queue metrics
ACTIVE_WORKERS = Gauge(
    "celery_active_workers",
    "Number of active celery worker tasks",
    registry=registry,
)

QUEUE_LENGTH = Gauge(
    "celery_queue_length",
    "Length of the celery default queue (approx)",
    registry=registry,
)


def observe_request(method: str, endpoint: str, status: int, start: float):
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=str(status)).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start)


def observe_ingest(duration: float):
    INGEST_DURATION.observe(duration)


def observe_retrieval(duration: float):
    RETRIEVAL_DURATION.observe(duration)


def observe_stream_ttfb(seconds: float):
    STREAM_TTFB.observe(seconds)


def observe_stream_full(seconds: float):
    STREAM_FULL.observe(seconds)


def observe_vector_search(seconds: float):
    VECTOR_SEARCH.observe(seconds)


def observe_embedding(seconds: float):
    EMBEDDING_DURATION.observe(seconds)


def incr_error(where: str):
    ERROR_COUNT.labels(where=where).inc()


def set_active_workers(n: int):
    ACTIVE_WORKERS.set(n)


def set_queue_length(n: int):
    QUEUE_LENGTH.set(n)


def metrics_response():
    # generate latest metrics payload
    return generate_latest(registry), CONTENT_TYPE_LATEST
