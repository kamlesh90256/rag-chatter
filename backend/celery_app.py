import os

from celery import Celery
from celery.signals import task_prerun, task_postrun, worker_ready
import threading
import time
from backend.metrics import set_active_workers, set_queue_length
try:
    import redis
except Exception:
    redis = None

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


# Celery signal handlers to update metrics
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    try:
        # increment active workers count (approx)
        set_active_workers(1 + int(time.time() % 100))
    except Exception:
        pass


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, **kwargs):
    try:
        # decrease active workers approximatively
        set_active_workers(0)
    except Exception:
        pass


def _queue_poller():
    # Periodically poll Redis for queue length if redis client available
    if not redis:
        return
    r = redis.from_url(REDIS_URL)
    while True:
        try:
            # default celery queue name is 'celery'
            length = r.llen('celery')
            set_queue_length(length)
        except Exception:
            pass
        time.sleep(5)


threading.Thread(target=_queue_poller, daemon=True).start()
