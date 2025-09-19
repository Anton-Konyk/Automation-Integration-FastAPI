import os
from datetime import timedelta
from celery import Celery
from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int, min_value: int = 1) -> int:
    """Parse positive int from env with a floor to min_value."""
    raw = os.getenv(name, str(default))
    try:
        val = int(raw)
    except ValueError:
        val = default
    return max(val, min_value)


BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
TZ = os.getenv("TZ", "Europe/Bratislava")
FETCH_EVERY_MIN = _int_env("FETCH_EVERY_MINUTES", 60, min_value=1)


celery = Celery(
    "users_crawler",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["app.tasks"],
)

celery.conf.update(
    timezone=TZ,
    enable_utc=True,
    # Retry broker connect until available
    broker_connection_retry_on_startup=True,
    # TTL for task results (avoid backend bloat)
    result_expires=3600,
    # Fairer distribution across workers
    worker_prefetch_multiplier=1,
)

celery.conf.broker_transport_options = {
    # 10 minutes; adjust to your task's worst-case runtime
    "visibility_timeout": 600
}

celery.conf.beat_schedule = {
    "fetch-users-interval": {
        "task": "app.tasks.fetch_and_save_users",
        "schedule": timedelta(minutes=FETCH_EVERY_MIN),
        "options": {"queue": "default"},
    }
}
