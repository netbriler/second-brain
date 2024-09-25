from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from reminders.models import Reminder


@receiver(
    post_delete,
    sender=Reminder,
)
def _reminder_post_delete(instance: Reminder, **kwargs) -> None:
    instance.periodic_task.delete()


@receiver(
    post_save,
    sender=Reminder,
)
def _reminder_post_save(instance: Reminder, **kwargs) -> None:
    if instance.periodic_task:
        instance.periodic_task.enabled = instance.is_enabled
        instance.periodic_task.save()
