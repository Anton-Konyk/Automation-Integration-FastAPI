from fastapi import FastAPI
from app.tasks import fetch_and_save_users

app = FastAPI(title="Users CSV Service Automation Integration")


@app.get("/")
def root():
    """Basic welcome endpoint"""
    return {"message": "Users CSV Service is running"}


@app.get("/health")
def health():
    """Simple healthcheck endpoint"""
    return {"status": "ok"}


@app.post("/trigger")
def trigger_task():
    """ Manually trigger the Celery task from HTTP.
        Useful for on-demand runs besides the scheduled Beat job.
    """
    result = fetch_and_save_users.delay()
    return {"task_id": result.id, "status": "queued"}
