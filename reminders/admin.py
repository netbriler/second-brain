from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from reminders import models
from utils.helpers import model_link


@admin.register(models.Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_link',
        'title',
        'description',
        'task_class',
        'is_enabled',
        'created_at',
        'updated_at',
    )

    list_select_related = ('user', 'periodic_task')

    search_fields = (
        'title',
        'description',
        'task_class',
        'is_enabled',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'created_at',
        'updated_at',
        AutocompleteFilterFactory(_('User'), 'user'),
        'is_enabled',
    )

    autocomplete_fields = ('user', 'periodic_task')

    list_display_links = ('id', 'title')

    readonly_fields = (
        'id',
        'periodic_task',
        'created_at',
        'updated_at',
    )

    def user_link(self, obj):
        if obj.user:
            return model_link(obj.user)
        return '-'

    user_link.short_description = _('User')

    @admin.action(description=_('Enable selected reminders'))
    def enable_selected_reminders(self, request, queryset):
        queryset.update(is_enabled=True)

    @admin.action(description=_('Disable selected reminders'))
    def disable_selected_reminders(self, request, queryset):
        queryset.update(is_enabled=False)

    actions = ['enable_selected_reminders', 'disable_selected_reminders']
