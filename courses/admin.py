from admin_auto_filters.filters import AutocompleteFilterFactory
from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from . import models
from .inlines import GroupInline, LessonEntityInline, LessonInline


@admin.register(models.Course)
class CourseAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
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

    ordering = (
        'id',
        'position',
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

    inlines = [GroupInline, LessonInline]


@admin.register(models.Group)
class GroupAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
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

    autocomplete_fields = ('parent', 'course')
    list_select_related = ('parent', 'course')

    list_filter = (
        'id',
        'title',
        'description',
        AutocompleteFilterFactory(_('Parent'), 'parent'),
        AutocompleteFilterFactory(_('Course'), 'course'),
        'created_at',
        'updated_at',
    )

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )

    ordering = (
        'id',
        'position',
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

    inlines = [GroupInline, LessonInline]


@admin.register(models.Lesson)
class LessonAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
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
        AutocompleteFilterFactory(_('Group'), 'group'),
        AutocompleteFilterFactory(_('Course'), 'course'),
        'created_at',
        'updated_at',
    )

    autocomplete_fields = ('group', 'course')
    list_select_related = ('group', 'course')

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )

    ordering = ('position',)

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

    inlines = [LessonEntityInline]


@admin.register(models.LessonEntity)
class LessonEntityAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'lesson',
        'content',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'id',
        'content',
    )

    list_select_related = ('lesson', 'file')
    autocomplete_fields = ('lesson', 'file')

    list_filter = (
        AutocompleteFilterFactory(_('Lesson'), 'lesson'),
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
                    'content',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    ordering = (
        'lesson',
        'position',
    )
