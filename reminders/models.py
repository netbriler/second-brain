from django.db import models
from django.utils.translation import gettext_lazy as _

from reminders.tasks_registry import choices


class Reminder(models.Model):
    class Meta:
        verbose_name = _('Reminder')
        verbose_name_plural = _('Reminders')

    user = models.ForeignKey(
        'users.User',
        related_name='reminders',
        on_delete=models.CASCADE,
        verbose_name=_('User'),
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('Title'),
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
    )

    task_class = models.CharField(
        max_length=200,
        verbose_name=_('Task Class'),
        choices=choices,
    )

    data = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Data'),
        default=dict,
    )

    periodic_task = models.ForeignKey(
        'django_celery_beat.PeriodicTask',
        related_name='reminders',
        on_delete=models.CASCADE,
        verbose_name=_('Periodic Task'),
        null=True,
        blank=True,
    )

    is_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Is Enabled'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    def __str__(self):
        return self.title
