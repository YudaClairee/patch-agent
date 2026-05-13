from celery import Celery

from src.core.config import settings

celery_app = Celery(
    "patch",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.autodiscover_tasks(["src.services.indexing"])

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "src.services.indexing.index_repository": {"queue": "indexing"},
    },
)