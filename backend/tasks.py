from .celery_app import celery_app


@celery_app.task(bind=True)
def long_running_ingest(self, source_url: str, metadata: dict | None = None):
    """Placeholder task to run ingestion asynchronously.

    Replace the internals to call your existing ingestion pipeline functions.
    """
    # Import here to avoid heavy imports at module import time
    try:
        from backend.ingest.pipeline import IngestionService
    except Exception:
        # If import fails in certain test environments, raise for visibility
        raise

    service = IngestionService()
    # Call the ingestion logic (this should be implemented in your pipeline)
    result = service.ingest_single(source_url, metadata=metadata or {})
    return result
