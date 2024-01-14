from django.db import models
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')

    title = models.CharField(
        max_length=200,
        verbose_name=_('Title'),
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    groups = models.ManyToManyField(
        'courses.Group',
        related_name='courses',
        verbose_name=_('Groups'),
    )

    def __str__(self):
        return self.title


class Group(models.Model):
    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')

    title = models.CharField(
        max_length=200,
        verbose_name=_('Title'),
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
    )

    parent = models.ForeignKey(
        'self',
        related_name='children',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('Parent Group'),
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


class Lesson(models.Model):
    class Meta:
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')

    title = models.CharField(
        max_length=200,
        verbose_name=_('Title'),
    )

    content = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Content'),
    )

    file = models.ForeignKey(
        'telegram_bot.File',
        related_name='lessons',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('File'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    groups = models.ManyToManyField(
        'courses.Group',
        related_name='lessons',
        verbose_name=_('Groups'),
    )

    def __str__(self):
        return self.title
