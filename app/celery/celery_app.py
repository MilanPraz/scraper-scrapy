from celery import Celery
from app.redis.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND


celery_app = Celery(
    "scraper-worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.scrape_tasks"
    ]
)

celery_app.conf.update(
    tassk_track_started=True,
    result_expires=3600,  # 1 hour
)

celery_app.autodiscover_tasks(["app.tasks"]) # Automatically discover tasks in the specified modules