import os
from celery import Celery

celery_app = Celery(
    "solardim",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    include=["backend.infrastructure.tasks"],
)
