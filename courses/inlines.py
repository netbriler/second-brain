from adminsortable2.admin import SortableInlineAdminMixin
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from courses import models


class GroupInline(SortableInlineAdminMixin, admin.TabularInline):
    model = models.Group
    extra = 1
    ordering = ['position']
    autocomplete_fields = ('parent', 'course')
    verbose_name = _('Group')
    verbose_name_plural = _('Groups')


class LessonInline(SortableInlineAdminMixin, admin.TabularInline):
    model = models.Lesson
    extra = 1
    ordering = ['position']
    autocomplete_fields = ('group', 'course')
    verbose_name = _('Lesson')
    verbose_name_plural = _('Lessons')


class LessonEntityInline(SortableInlineAdminMixin, admin.TabularInline):
    model = models.LessonEntity
    extra = 1
    ordering = ['position']
    autocomplete_fields = ('file',)
    verbose_name = _('Lesson Entity')
    verbose_name_plural = _('Lesson Entities')


class LinkInline(SortableInlineAdminMixin, admin.TabularInline):
    model = models.Link
    extra = 1
    ordering = ['position']
    autocomplete_fields = ('lesson_entity',)
    verbose_name = _('Link')
    verbose_name_plural = _('Links')
