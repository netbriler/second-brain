from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from . import models
from .inlines import CourseGroupInline, GroupCourseInline, LessonGroupInline


@admin.register(models.Course)
class CourseAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'description',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'id',
        'name',
        'description',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'id',
        'name',
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
            'Main',
            {
                'fields': [
                    'id',
                    'name',
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
        'name',
        'description',
        'parent',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'id',
        'name',
        'description',
        'parent',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'id',
        'name',
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
            'Main',
            {
                'fields': [
                    'id',
                    'name',
                    'description',
                    'parent',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    inlines = [LessonGroupInline, GroupCourseInline]


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
            'Main',
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
