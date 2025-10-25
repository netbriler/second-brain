from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from utils.helpers import model_link

from .models import Account


@admin.register(Account)
class AccountAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'phone',
        'user_link',
    )

    search_fields = (
        'name',
        'phone',
        'user',
    )

    list_filter = (
        'name',
        'phone',
        AutocompleteFilterFactory(_('User'), 'user'),
    )

    list_select_related = ('user',)

    readonly_fields = (
        'id',
        'name',
        'phone',
        'user',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def user_link(self, obj):
        if obj.user:
            return model_link(obj.user)
        return '-'

    user_link.short_description = _('User')
