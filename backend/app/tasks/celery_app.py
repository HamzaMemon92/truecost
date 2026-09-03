from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery("truecost", broker=settings.redis_url, backend=settings.redis_url, include=["app.tasks.price_watches", "app.tasks.provider_connections"])
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "evaluate-price-watches": {
            "task": "truecost.evaluate_price_watches",
            "schedule": settings.price_watch_interval_seconds,
        },
        "deliver-notification-outbox": {
            "task": "truecost.deliver_notification_outbox",
            "schedule": 20.0,
        },
        "reconcile-expo-receipts": {
            "task": "truecost.reconcile_expo_receipts",
            "schedule": 60.0,
        },
        "retry-broker-revocations": {
            "task": "truecost.retry_broker_revocations",
            "schedule": 60.0,
        },
    },
)
