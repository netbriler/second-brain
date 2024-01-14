from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from . import models


@admin.register(models.File)
class CourseAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'content_type',
        'title',
        'file_id',
        'thumbnail_id',
        'created_at',
        'updated_at',
        'uploaded_by',
    )

    list_select_related = ('uploaded_by',)

    search_fields = (
        'id',
        'content_type',
        'title',
        'file_id',
        'thumbnail_id',
        'created_at',
        'updated_at',
        'uploaded_by',
    )

    list_filter = (
        'id',
        'content_type',
        'title',
        'file_id',
        'thumbnail_id',
        'created_at',
        'updated_at',
        'uploaded_by',
    )

    readonly_fields = (
        'id',
        'content_type',
        'title',
        'file_id',
        'thumbnail_id',
        'raw_data',
        'created_at',
        'updated_at',
        'uploaded_by',
    )

    fieldsets = [
        (
            'Main',
            {
                'fields': [
                    'id',
                    'content_type',
                    'title',
                    'file_id',
                    'thumbnail_id',
                    'raw_data',
                    'created_at',
                    'updated_at',
                    'uploaded_by',
                ],
            },
        ),
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
