import os

from celery import Celery

# Broker URL uses Redis; default to docker-compose service
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "backend_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Example Celery configuration; tune as needed
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    worker_prefetch_multiplier=1,
)

if __name__ == "__main__":
    celery_app.start()
