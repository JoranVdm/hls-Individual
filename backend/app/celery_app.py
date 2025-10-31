from celery import Celery
import os

broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
cel = Celery("transcoder", broker=broker, backend=broker)
cel.conf.task_serializer = 'json'
cel.conf.accept_content = ['json']
cel.conf.result_serializer = 'json'

