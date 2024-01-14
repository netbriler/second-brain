from django.db import models
from django.utils.translation import gettext_lazy as _

from telegram_bot.constants import FILE_CONTENT_TYPES


class File(models.Model):
    class Meta:
        verbose_name = _('File')
        verbose_name_plural = _('Files')

    content_type = models.CharField(
        max_length=200,
        choices=FILE_CONTENT_TYPES,
        verbose_name=_('Content Type'),
    )

    title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Title'),
    )

    file_id = models.CharField(
        max_length=200,
        verbose_name=_('File ID'),
    )

    thumbnail_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Thumbnail ID'),
    )

    raw_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Raw Data'),
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
        return f'{self.get_content_type_display()} {self.title or self.file_id}'
