from app.celery import LoggingTask, app
from utils.logging import logger


@app.task(base=LoggingTask)
def reminders():
    logger.info('Test task executed successfully!')
    return 'Task completed'
