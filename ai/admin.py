from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from ai import models
from utils.helpers import model_link


@admin.register(models.Message)
class MessageAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'text',
        'prompt',
        'response',
        'category',
        'time_spent',
        'source_link',
        'requested_by_link',
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
        'category',
        'source_id',
        'created_at',
        'updated_at',
        AutocompleteFilterFactory(_('Requested By'), 'requested_by'),
    )

    readonly_fields = (
        'id',
        'text',
        'prompt',
        'response',
        'category',
        'time_spent',
        'source_link',
        'requested_by',
        'created_at',
        'updated_at',
    )

    list_display_links = ('id', 'text')

    list_select_related = ('requested_by',)

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
                    'source_link',
                    'requested_by',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    def source_link(self, obj):
        return model_link(obj.source)

    source_link.short_description = _('Source')

    def requested_by_link(self, obj):
        return model_link(obj.source)

    requested_by_link.short_description = _('Requested By')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
