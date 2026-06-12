from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "chatapp",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.image_tasks", "app.tasks.message_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)