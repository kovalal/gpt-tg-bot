from celery_app import celery_app
import logging
from dt.create import save_message_to_db  # Replace with actual DB logic
import json
from clients.db import Session

logger = logging.getLogger("DatabaseWorker")


@celery_app.task
def save_message_task(**kwargs):
    save_message_to_db(kwargs)
