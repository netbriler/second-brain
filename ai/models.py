from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from ai.constants import AIMessageCategories


class Message(models.Model):
    text = models.TextField(
        verbose_name=_('Text'),
    )

    prompt = models.TextField(
        verbose_name=_('Prompt'),
        null=True,
        blank=True,
    )

    response = models.TextField(
        verbose_name=_('Response'),
        null=True,
        blank=True,
    )

    category = models.CharField(
        max_length=50,
        choices=[(category.value[0], category.label) for category in AIMessageCategories],
        verbose_name=_('Category'),
    )

    time_spent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Time Spent'),
        null=True,
        blank=True,
    )

    source_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        related_name='+',
        null=True,
        editable=False,
        verbose_name=_('Source Type'),
    )

    source_id = models.BigIntegerField(
        null=True,
        editable=False,
        verbose_name=_('Source ID'),
    )

    source = GenericForeignKey('source_type', 'source_id')

    requested_by = models.ForeignKey(
        'users.User',
        related_name='ai_messages',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('Requested By'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')

    def __str__(self):
        return f'AI message {self.id}'
