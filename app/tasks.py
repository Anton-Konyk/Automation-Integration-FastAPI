import csv
import os
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import requests
from app.celery_app import celery
from celery.utils.log import get_task_logger


USERS_API_URL = os.getenv(
    "USERS_API_URL",
    "https://jsonplaceholder.typicode.com/users"
)
CSV_DIR = os.getenv("CSV_DIR", os.path.join(os.getcwd(), "data"))
TZ = os.getenv("TZ", "Europe/Bratislava")

try:
    TZ_INFO = ZoneInfo(TZ)
except ZoneInfoNotFoundError:
    logger = get_task_logger(__name__)
    logger.warning("TZ '%s' not found; falling back to UTC", TZ)
    TZ_INFO = ZoneInfo("UTC")

logger = get_task_logger(__name__)


@celery.task(
    bind=True,
    name="app.tasks.fetch_and_save_users",
    autoretry_for=(requests.RequestException,),
    retry_backoff=True,        # exponential backoff: 1s, 2s, 4s, ...
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def fetch_and_save_users(self) -> str:
    """
    Fetch users from external API and save selected fields into a CSV file.
    The CSV will contain: id, name, email
    """

    resp = requests.get(
        USERS_API_URL,
        timeout=(5, 30),
        headers={"Accept": "application/json"}
    )
    resp.raise_for_status()

    try:
        users = resp.json()
    except ValueError as e:
        raise ValueError("Failed to parse JSON from USERS_API_URL") from e

    if not isinstance(users, list):
        raise ValueError(
            "Unexpected response format: expected a list of users"
        )

    date_str = datetime.now(TZ_INFO).strftime("%Y%m%d-%H%M")
    task_uuid = (getattr(self.request, "id", None) or uuid.uuid4().hex)
    short_uuid = task_uuid.replace("-", "")[:12]

    os.makedirs(CSV_DIR, exist_ok=True)
    path = os.path.join(CSV_DIR, f"users-{date_str}-{short_uuid}.csv")

    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "email"])
        for u in users:
            writer.writerow([u.get("id"), u.get("name"), u.get("email")])
    os.replace(tmp, path)

    logger.info("Saved %d users to %s", len(users), path)
    return path
