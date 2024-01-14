from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from . import models
from .inlines import (
    CourseGroupInline,
    GroupCourseInline,
    GroupLessonInline,
    LessonGroupInline,
)


@admin.register(models.Course)
class CourseAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'description',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'id',
        'title',
        'description',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'id',
        'title',
        'description',
        'created_at',
        'updated_at',
    )

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )

    fieldsets = [
        (
            _('General'),
            {
                'fields': [
                    'id',
                    'title',
                    'description',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    inlines = [CourseGroupInline]


@admin.register(models.Group)
class GroupAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'description',
        'parent',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'id',
        'title',
        'description',
        'parent',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'id',
        'title',
        'description',
        'parent',
        'created_at',
        'updated_at',
    )

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )

    fieldsets = [
        (
            _('General'),
            {
                'fields': [
                    'id',
                    'title',
                    'description',
                    'parent',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    inlines = [GroupLessonInline, GroupCourseInline]


@admin.register(models.Lesson)
class LessonAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'id',
        'title',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'id',
        'title',
        'created_at',
        'updated_at',
    )

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )

    fieldsets = [
        (
            _('General'),
            {
                'fields': [
                    'id',
                    'title',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    inlines = [LessonGroupInline]
