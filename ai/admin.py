from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.html import format_html
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
        if obj.source:
            content_type = ContentType.objects.get_for_model(obj.source)
            url = reverse(
                f'admin:{content_type.app_label}_{content_type.model}_change',
                args=[obj.source.pk],
            )
            return format_html(
                '<a href="{url}">{text}</a>',
                url=url,
                text=str(obj.source),
            )
        return '-'

    source_link.short_description = _('Source')

    def requested_by_link(self, obj):
        if obj.requested_by:
            url = reverse(
                'admin:users_user_change',
                args=[obj.requested_by.pk],
            )
            return format_html(
                '<a href="{url}">{text}</a>',
                url=url,
                text=str(obj.requested_by),
            )
        return '-'

    requested_by_link.short_description = _('Requested By')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
