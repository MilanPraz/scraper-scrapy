from celery import Celery
from celery.schedules import crontab
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
    task_track_started=True,
    result_expires=3600,  # 1 hour
    timezone="Asia/Kathmandu"
)

# celery_app.autodiscover_tasks(["app. "]) # Automatically discover tasks in the specified modules

celery_app.conf.beat_schedule={
    "scrape-hukut-mobiles-every-5-minutes": {
        "task":"scraper.run_spider",
        "schedule": crontab(minute=0, hour="*/6"),
        "args":('hukut','mobiles','all')
    },
    "scrape-yantra-mobiles-every-5-minutes":{
        "task":"scraper.run_spider",
        "schedule":crontab(minute=15,hour="*/6"),
        "args":('yantra','mobiles','all')
    },
    "scrape-mobile-mandu-mobiles-every-5-minutes":{
        "task":"scraper.run_spider",
        "schedule": crontab(minute=30, hour="*/6"),
        "args":('mobilemandu','mobiles','all')
    }
}