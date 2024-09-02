from admin_auto_filters.filters import AutocompleteFilterFactory
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
        'requested_by',
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
        'requested_by',
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
        AutocompleteFilterFactory('Requested By', 'requested_by'),
    )

    readonly_fields = (
        'id',
        'text',
        'prompt',
        'response',
        'category',
        'time_spent',
        'source',
        'requested_by',
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
                    'requested_by',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]
