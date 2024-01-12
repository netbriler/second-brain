from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from . import models


@admin.register(models.User)
class UserAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'telegram_id',
        'telegram_username',
        'language_code',
        'first_name',
        'last_name',
        'is_superuser',
        'is_active',
        'telegram_is_active',
        'telegram_activity_at',
    )

    search_fields = (
        'id',
        'username',
        'telegram_id',
        'telegram_username',
        'language_code',
        'first_name',
        'last_name',
        'is_superuser',
        'is_active',
        'telegram_is_active',
        'telegram_activity_at',
    )

    list_filter = (
        'id',
        'username',
        'telegram_id',
        'telegram_username',
        'language_code',
        'first_name',
        'last_name',
        'is_superuser',
        'is_active',
        'telegram_is_active',
        'telegram_activity_at',
    )

    readonly_fields = (
        'id',
        'username',
        'telegram_username',
        'language_code',
        'first_name',
        'last_name',
        'is_superuser',
        'telegram_is_active',
        'telegram_activity_at',
    )

    fieldsets = (
        ('Main', {
            'fields': (
                'id',
                'username',
                'language_code',
                'first_name',
                'last_name',
            ),
        }),
        ('Permissions', {
            'fields': (
                'is_superuser',
                'is_active',
                'groups',
                'user_permissions',
            ),
        }),
        ('Telegram', {
            'fields': (
                'telegram_id',
                'telegram_username',
                'telegram_is_active',
                'telegram_activity_at',
            ),
        }),
    )
