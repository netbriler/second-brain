from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from reminders import models


@admin.register(models.Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'title',
        'description',
        'task_class',
        'created_at',
        'updated_at',
    )

    list_select_related = ('user', 'periodic_task')

    search_fields = (
        'id',
        'title',
        'description',
        'task_class',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'created_at',
        'updated_at',
        AutocompleteFilterFactory(_('User'), 'user'),
    )

    autocomplete_fields = ('user', 'periodic_task')

    list_display_links = ('id', 'user', 'title')

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )
