from celery import Celery

from app.config import settings

celery_app = Celery(
    "growthOS",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.execution",
        "app.workers.email_tasks",
        "app.workers.optimization_tasks",
        "app.workers.metrics_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "optimization-every-24h": {
            "task": "run_optimization_for_all_campaigns",
            "schedule": 86400,
        },
        "metrics-snapshot-hourly": {
            "task": "sync_metrics_for_all_campaigns",
            "schedule": 3600,
        },
    },
)
