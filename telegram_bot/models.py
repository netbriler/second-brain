from django.db import models

from telegram_bot.constants import FILE_CONTENT_TYPES


class File(models.Model):
    content_type = models.CharField(
        max_length=200,
        choices=FILE_CONTENT_TYPES,
    )

    title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )

    file_id = models.CharField(
        max_length=200,
    )

    thumbnail_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )

    raw_data = models.JSONField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    uploaded_by = models.ForeignKey(
        'users.User',
        related_name='files',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'{self.get_content_type_display()} {self.title or self.file_id}'
