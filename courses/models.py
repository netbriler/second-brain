from django.db import models
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')

    position = models.PositiveIntegerField(
        default=100,
        blank=False,
        null=False,
        verbose_name=_('Position'),
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


class Group(models.Model):
    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')

    position = models.PositiveIntegerField(
        default=100,
        blank=False,
        null=False,
        verbose_name=_('Position'),
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

    course = models.ForeignKey(
        'courses.Course',
        related_name='groups',
        on_delete=models.CASCADE,
        verbose_name=_('Course'),
        null=True,
        blank=True,
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

    position = models.PositiveIntegerField(
        default=100,
        blank=False,
        null=False,
        verbose_name=_('Position'),
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('Title'),
    )

    course = models.ForeignKey(
        'courses.Course',
        related_name='lessons',
        on_delete=models.CASCADE,
        verbose_name=_('Course'),
        null=True,
        blank=True,
    )

    group = models.ForeignKey(
        'courses.Group',
        related_name='lessons',
        on_delete=models.CASCADE,
        verbose_name=_('Group'),
        null=True,
        blank=True,
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


class LessonEntity(models.Model):
    class Meta:
        verbose_name = _('Lesson Entity')
        verbose_name_plural = _('Lesson Entities')

    position = models.PositiveIntegerField(
        default=100,
        blank=False,
        null=False,
        verbose_name=_('Position'),
    )

    content = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Content'),
    )

    file = models.ForeignKey(
        'telegram_bot.File',
        related_name='lesson_entities',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('File'),
    )

    lesson = models.ForeignKey(
        'courses.Lesson',
        related_name='lesson_entities',
        on_delete=models.CASCADE,
        verbose_name=_('Lesson'),
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
        return self.content
