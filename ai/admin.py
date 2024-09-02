from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from ai import models


@admin.register(models.Message)
class MessageAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'text',
        'prompt',
        'response',
        'category',
        'time_spent',
        'source',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'id',
        'text',
        'prompt',
        'response',
        'category',
        'time_spent',
        'source',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'id',
        'category',
        'time_spent',
        'source_id',
        'created_at',
        'updated_at',
    )

    readonly_fields = (
        'id',
        'text',
        'prompt',
        'response',
        'category',
        'time_spent',
        'source',
        'created_at',
        'updated_at',
    )

    fieldsets = [
        (
            _('General'),
            {
                'fields': [
                    'id',
                    'text',
                    'prompt',
                    'response',
                    'category',
                    'time_spent',
                    'source',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]
