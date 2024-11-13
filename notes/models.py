from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class Note(models.Model):
    class Meta:
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        blank=True,
        null=True,
    )

    text = models.TextField(
        verbose_name=_('Text'),
    )

    summary = models.TextField(
        verbose_name=_('Summary'),
        blank=True,
        null=True,
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

    related_notes = models.ManyToManyField(
        'self',
        blank=True,
        verbose_name=_('Related Notes'),
    )

    user = models.ForeignKey(
        'users.User',
        related_name='notes',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('User'),
    )

    STATUS_CHOICES = [
        ('active', _('Active')),
        ('archived', _('Archived')),
        ('deleted', _('Deleted')),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=_('Status'),
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_('Is Deleted'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    tags = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Tags'),
        help_text=_('Comma-separated tags for categorizing notes'),
    )

    def __str__(self):
        return f'Note {self.id}: {self.text[:20]}...'

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
