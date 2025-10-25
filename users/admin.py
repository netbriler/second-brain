from django.contrib import admin
from django.utils.translation import gettext_lazy as _
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
        'first_name',
        'last_name',
        'telegram_is_active',
        'telegram_activity_at',
    )

    fieldsets = (
        (
            _('General'),
            {
                'fields': (
                    'id',
                    'username',
                    'language_code',
                    'first_name',
                    'last_name',
                ),
            },
        ),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_superuser',
                    'is_active',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (
            _('Telegram'),
            {
                'fields': (
                    'telegram_id',
                    'telegram_username',
                    'telegram_is_active',
                    'telegram_activity_at',
                ),
            },
        ),
    )
