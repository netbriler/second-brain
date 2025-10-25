from django.core.exceptions import ValidationError
from django.db import models
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from telegram_bot.constants import FileContentType
from utils.helpers import AutoIncrementalField


class Course(models.Model):
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        ordering = ('position',)

    position = AutoIncrementalField(
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

    thumbnail = models.ForeignKey(
        'telegram_bot.File',
        related_name='course_thumbnails',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Thumbnail'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    def clean(self):
        if self.thumbnail and self.thumbnail.content_type != FileContentType.PHOTO:
            raise ValidationError(_('Thumbnail must be a photo'))

    def __str__(self):
        return self.title


class Group(models.Model):
    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')
        ordering = ('position',)

    position = AutoIncrementalField(
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

    thumbnail = models.ForeignKey(
        'telegram_bot.File',
        related_name='group_thumbnails',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Thumbnail'),
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

    def clean(self):
        if self.parent and self.parent.course and self.course and self.parent.course != self.course:
            raise ValidationError(_('Parent group must belong to the same course'))

        if self.thumbnail and self.thumbnail.content_type != FileContentType.PHOTO:
            raise ValidationError(_('Thumbnail must be a photo'))

    def save(
        self,
        *args,
        **kwargs,
    ):
        if self.parent and not self.course and self.parent.course:
            self.course = self.parent.course

        return super().save(
            *args,
            **kwargs,
        )

    def __str__(self):
        return self.title


class Lesson(models.Model):
    class Meta:
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')
        ordering = ('position',)

    position = AutoIncrementalField(
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

    thumbnail = models.ForeignKey(
        'telegram_bot.File',
        related_name='lesson_thumbnails',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Thumbnail'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    def clean(self):
        if self.group and self.course and self.group.course and self.group.course != self.course:
            raise ValidationError(_('Group must belong to the same course'))

        if self.thumbnail and self.thumbnail.content_type != FileContentType.PHOTO:
            raise ValidationError(_('Thumbnail must be a photo'))

    def save(
        self,
        *args,
        **kwargs,
    ):
        if self.group and not self.course and self.group.course:
            self.course = self.group.course

        return super().save(
            *args,
            **kwargs,
        )

    def __str__(self):
        return self.title


class Link(models.Model):
    class Meta:
        verbose_name = _('Link')
        verbose_name_plural = _('Links')
        ordering = ('position',)

    position = AutoIncrementalField(
        verbose_name=_('Position'),
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('Title'),
    )

    url = models.URLField(
        verbose_name=_('URL'),
    )

    course = models.ForeignKey(
        'courses.Course',
        related_name='links',
        on_delete=models.CASCADE,
        verbose_name=_('Course'),
        blank=True,
        null=True,
    )

    group = models.ForeignKey(
        'courses.Group',
        related_name='links',
        on_delete=models.CASCADE,
        verbose_name=_('Group'),
        blank=True,
        null=True,
    )

    lesson = models.ForeignKey(
        'courses.Lesson',
        related_name='links',
        on_delete=models.CASCADE,
        verbose_name=_('Lesson'),
        blank=True,
        null=True,
    )

    lesson_entity = models.ForeignKey(
        'courses.LessonEntity',
        related_name='links',
        on_delete=models.CASCADE,
        verbose_name=_('Lesson Entity'),
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    def clean(self):
        fields = [self.course, self.group, self.lesson, self.lesson_entity]
        if not any(fields):
            raise ValidationError(_('At least one of course, group, lesson, or lesson_entity must be set'))

    def __str__(self):
        return self.title


class LessonEntity(models.Model):
    class Meta:
        verbose_name = _('Lesson Entity')
        verbose_name_plural = _('Lesson Entities')
        ordering = ('position',)

    position = AutoIncrementalField(
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

    @property
    def content_short(self):
        text = strip_tags(self.content.split('\n')[0]) if self.content else ''
        return text[:30] + ('...' if len(text) > 30 else '') if self.content else ''

    def __str__(self):
        return self.content_short


class LearningProgress(models.Model):
    class Meta:
        verbose_name = _('Learning Progress')
        verbose_name_plural = _('Learning Progresses')
        ordering = ('-updated_at',)

    user = models.ForeignKey(
        'users.User',
        related_name='progresses',
        on_delete=models.CASCADE,
        verbose_name=_('User'),
    )

    course = models.ForeignKey(
        'courses.Course',
        related_name='progresses',
        on_delete=models.CASCADE,
        verbose_name=_('Course'),
        blank=True,
        null=True,
    )

    lesson = models.ForeignKey(
        'courses.Lesson',
        related_name='progresses',
        on_delete=models.CASCADE,
        verbose_name=_('Lesson'),
    )

    lesson_entity = models.ForeignKey(
        'courses.LessonEntity',
        related_name='progresses',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('Lesson Entity'),
    )

    timecode = models.BigIntegerField(
        default=0,
        verbose_name=_('Timecode (in seconds)'),
    )

    is_finished = models.BooleanField(
        default=False,
        verbose_name=_('Is Finished'),
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
        return f'{self.user_id=} - {self.course_id=} - {self.lesson_id=}'
