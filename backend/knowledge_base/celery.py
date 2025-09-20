"""
Celery configuration for knowledge_base project.
"""

import os

from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "knowledge_base.settings")

app = Celery("knowledge_base")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    "cleanup-temp-files": {
        "task": "apps.documents.tasks.cleanup_temp_files",
        "schedule": 3600.0,  # Run every hour
    },
    "update-ml-models": {
        "task": "apps.classification.tasks.update_ml_models",
        "schedule": 86400.0,  # Run daily
    },
    "generate-reports": {
        "task": "apps.monitoring.tasks.generate_daily_report",
        "schedule": 86400.0,  # Run daily
    },
}

app.conf.timezone = "Asia/Shanghai"


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
