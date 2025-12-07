from celery import Celery
import os

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_BACKEND_URL = os.environ.get("CELERY_BACKEND_URL", "redis://redis:6379/0")

cel = Celery(
    "worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL
)

cel.conf.task_serializer = 'json'
cel.conf.accept_content = ['json']
cel.conf.result_serializer = 'json'
cel.conf.timezone = 'UTC'

# Autodiscover tasks
cel.autodiscover_tasks(['taskFolder', 'tasks'])

# Ensure tasks module is loaded (fallback for import issues)
import taskFolder.cache_tasks
import tasks

# Celery Beat schedule for cache refresh every 5 min
cel.conf.beat_schedule = {
    "refresh-show-cache-every-5-min": {
        "task": "taskFolder.cache_tasks.refresh_show_cache",
        "schedule": 300,  # seconds
    }
}
