import json

from django_celery_beat.models import CrontabSchedule, PeriodicTask

from reminders.models import Reminder
from reminders.task_base import ReminderTaskBase
from users.models import User


async def create_reminder(
    user: User,
    title: str,
    crontab_string: str,
    task_class: ReminderTaskBase | str,
    description: str = '',
    data: dict = None,
):
    if isinstance(task_class, str):
        task_class = ReminderTaskBase.get_task_class_from_str(task_class)
    if not issubclass(task_class, ReminderTaskBase):
        raise TypeError('Invalid task class. Task class must be subclass of Reminder')

    try:
        minute, hour, day_of_month, month_of_year, day_of_week = crontab_string.split()
    except ValueError:
        raise ValueError(
            'Invalid crontab string format. Expected format: "minute hour day_of_month month_of_year day_of_week"',
        )

    crontab_schedule, _ = await CrontabSchedule.objects.aget_or_create(
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        day_of_week=day_of_week,
    )

    reminder = await Reminder.objects.acreate(
        user=user,
        title=title,
        description=description,
        task_class=ReminderTaskBase.get_task_class_str(task_class),
        data=data,
    )

    periodic_task = await PeriodicTask.objects.acreate(
        crontab=crontab_schedule,
        name=f'Reminder: task {reminder.id}',
        task='reminders.tasks.execute_reminder_task',
        args=json.dumps([reminder.id]),
    )
    reminder.periodic_task = periodic_task
    await reminder.asave()

    return reminder
