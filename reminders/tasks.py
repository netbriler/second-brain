from app.celery import LoggingTask, app
from reminders.models import Reminder
from reminders.task_base import ReminderTaskBase


@app.task(base=LoggingTask)
def execute_reminder_task(reminder_id: int, *args, **kwargs):
    reminder = Reminder.objects.get(id=reminder_id)
    task_class = ReminderTaskBase.get_task_class_from_str(reminder.task_class)

    task = task_class(reminder)
    task.run()
