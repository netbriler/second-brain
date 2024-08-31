import os

from celery import Celery, Task
from django.conf import settings

from utils.logging import logger

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')


class LoggingTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.exception(f'Task failed: {exc}', exc_info=exc)
        super().on_failure(exc, task_id, args, kwargs, einfo)


app = Celery('app')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
