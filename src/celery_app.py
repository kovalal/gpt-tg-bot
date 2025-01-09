from celery import Celery

# Initialize Celery app
celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",  # Redis as broker
    backend="redis://localhost:6379/1"  # Redis as result backend
)

# Celery configuration
celery_app.conf.task_routes = {
    "tasks.process_message": {"queue": "celery"}
}
celery_app.conf.timezone = "UTC"

celery_app.autodiscover_tasks(["tasks"])

import tasks.messages
import tasks.database