from .celery_app import celery_app


@celery_app.task(bind=True)
def ingest_pair_task(self, youtube_url: str | None, instagram_url: str | None):
    """Celery task to run `IngestionService.ingest_pair` inside a DB session.

    Returns the ingestion result (or raises) and stores status in Celery result backend.
    """
    # import inside task to avoid heavy imports at module import time
    from sqlmodel import Session
    from backend.utils.database import engine
    from backend.ingest.pipeline import IngestionService

    with Session(engine) as session:
        service = IngestionService(session)
        result = service.ingest_pair(youtube_url or "", instagram_url or "")
    return result
