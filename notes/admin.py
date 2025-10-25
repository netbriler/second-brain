from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from utils.helpers import model_link

from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'text', 'summary', 'user_link', 'source_link', 'status', 'is_deleted', 'created_at', 'updated_at',
    )

    list_display_links = ('id', 'title')

    list_filter = (
        'title', 'text', 'summary',
        AutocompleteFilterFactory(_('User'), 'user'),
        'status', 'is_deleted', 'created_at', 'updated_at', 'tags',
    )

    search_fields = ('title', 'text', 'summary', 'tags')

    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    readonly_fields = ('created_at', 'updated_at', 'source_link', 'source')

    fieldsets = (
        (None, {
            'fields': ('title', 'text', 'summary', 'related_notes', 'user', 'source_link', 'tags'),
        }),
        ('Status', {
            'fields': ('status', 'is_deleted'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    filter_horizontal = ('related_notes',)

    autocomplete_fields = ('user',)

    actions = ['mark_as_deleted', 'mark_as_active', 'mark_as_archived']

    def source_link(self, obj):
        return model_link(obj.source)

    source_link.short_description = _('Source')

    def user_link(self, obj):
        if obj.user:
            return model_link(obj.user)
        return '-'

    user_link.short_description = _('User')

    def mark_as_deleted(self, request, queryset):
        queryset.update(status='deleted', is_deleted=True)

    mark_as_deleted.short_description = _('Mark selected notes as deleted')

    def mark_as_active(self, request, queryset):
        queryset.update(status='active', is_deleted=False)

    mark_as_active.short_description = _('Mark selected notes as active')

    def mark_as_archived(self, request, queryset):
        queryset.update(status='archived', is_deleted=False)

    mark_as_archived.short_description = _('Mark selected notes as archived')
