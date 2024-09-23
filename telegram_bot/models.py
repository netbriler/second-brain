from django.db import models
from django.utils.translation import gettext_lazy as _

from telegram_bot.constants import FILE_CONTENT_TYPES, MessageRoles


class File(models.Model):
    class Meta:
        verbose_name = _('File')
        verbose_name_plural = _('Files')

    content_type = models.CharField(
        max_length=200,
        choices=FILE_CONTENT_TYPES,
        verbose_name=_('Content Type'),
    )

    file_id = models.CharField(
        max_length=200,
        verbose_name=_('File ID'),
    )

    file_unique_id = models.CharField(
        max_length=200,
        verbose_name=_('File Unique ID'),
        null=True,
        blank=True,
    )

    mime_type = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('MIME Type'),
    )

    raw_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Raw Data'),
    )

    caption = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Caption'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    uploaded_by = models.ForeignKey(
        'users.User',
        related_name='files',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('Uploaded By'),
    )

    def __str__(self):
        return f'Telegram file {self.get_content_type_display()} {self.id}'


class Message(models.Model):
    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')

    message_id = models.BigIntegerField(
        verbose_name=_('Message ID'),
    )

    chat_id = models.BigIntegerField(
        verbose_name=_('Chat ID'),
    )

    text = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Text'),
    )

    raw_data = models.JSONField(
        verbose_name=_('Raw Data'),
        default=dict,
    )

    file = models.ForeignKey(
        'telegram_bot.File',
        related_name='messages',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('File'),
    )

    role = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        choices=[(role.value[0], role.label) for role in MessageRoles],
        verbose_name=_('Role'),
    )

    user = models.ForeignKey(
        'users.User',
        related_name='messages',
        on_delete=models.CASCADE,
        verbose_name=_('User'),
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
        return f'Telegram message {self.id}'
