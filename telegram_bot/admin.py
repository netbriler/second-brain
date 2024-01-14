from asgiref.sync import async_to_sync
from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from telegram_bot.start_bot import default_bot

from . import models
from .services.files import send_file_to_user


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

    actions = [
        'send_to_telegram',
    ]

    @admin.action(description='Send to telegram')
    def send_to_telegram(self, request, queryset):
        for file in queryset:
            async_to_sync(send_file_to_user)(default_bot, file, request.user)

        self.message_user(request, 'Done')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
