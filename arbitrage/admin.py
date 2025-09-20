from copy import deepcopy

from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from totalsum.admin import TotalsumAdmin

from utils.helpers import model_link, format_number
from .forms import UserForm, ExchangeCredentialsAdminForm
from .models import Exchange, TradingPair, ArbitrageDealItem, ArbitrageDeal, ExchangeCredentials
from .resources import ArbitrageDealItemResource, ArbitrageDealFullResource


class ExchangeCredentialsInline(admin.TabularInline):
    model = ExchangeCredentials
    extra = 0
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'api_key',
                'is_enabled',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Exchange)
class ExchangeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name', 'is_enabled', 'created_at', 'updated_at')
    list_filter = (
        'is_enabled',
        'created_at',
        'updated_at',
    )
    fieldsets = (
        (None, {
            'fields': ('name', 'is_enabled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [ExchangeCredentialsInline]
    readonly_fields = ('created_at', 'updated_at',)
    search_fields = ('name',)


@admin.register(ExchangeCredentials)
class ExchangeCredentialsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    form = ExchangeCredentialsAdminForm

    list_display = (
        'exchange',
        'user',
        'api_key',
        'is_enabled',
        'created_at',
        'updated_at'
    )

    list_filter = (
        AutocompleteFilterFactory(_('Exchange'), 'exchange'),
        AutocompleteFilterFactory(_('User'), 'user'),
        'is_enabled',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Credentials', {
            'fields': (
                'exchange',
                'user',
                'api_key',
                'api_secret',
                'is_enabled',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at',)
    autocomplete_fields = ('exchange', 'user')
    search_fields = ('exchange__name', 'user__username')


@admin.register(TradingPair)
class TradingPairAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('base_currency', 'quote_currency', 'symbol', 'created_at', 'updated_at')
    list_filter = (
        'base_currency',
        'quote_currency',
        'created_at',
        'updated_at',
    )
    fieldsets = (
        (None, {
            'fields': ('base_currency', 'quote_currency', 'symbol')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'symbol')
    search_fields = ('symbol', 'base_currency', 'quote_currency')


@admin.register(ArbitrageDealItem)
class ArbitrageDealItemAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = ArbitrageDealItemResource

    def pnl_short(self, obj):
        return format_number(obj.pnl)

    pnl_short.short_description = _('PnL')

    def income_short(self, obj):
        return format_number(obj.income)

    income_short.short_description = _('Income')

    def roi_short(self, obj):
        return format_number(obj.roi)

    roi_short.short_description = _('ROI')

    def roi_percent_short(self, obj):
        return format_number(obj.roi_percent)

    roi_percent_short.short_description = _('ROI %')

    def margin_open_short(self, obj):
        return format_number(obj.margin_open)

    margin_open_short.short_description = _('Margin Open')

    def margin_close_short(self, obj):
        return format_number(obj.margin_close)

    margin_close_short.short_description = _('Margin Close')

    list_select_related = ('trading_pair', 'exchange', 'user')

    list_display = (
        'user', 'trading_pair', 'exchange', 'side',
        'open_price', 'close_price',
        'volume', 'leverage', 'fees', 'funding',
        'is_liquidated',
        'pnl_short', 'income_short', 'roi_percent_short',
        'duration', 'human_duration'
    )

    readonly_fields = (
        'pnl_short', 'margin_open_short', 'margin_close_short',
        'income_short', 'roi_short', 'roi_percent_short',
        'duration', 'human_duration',
        'created_at', 'updated_at',
    )

    list_filter = (
        AutocompleteFilterFactory(_('User'), 'user'),
        AutocompleteFilterFactory(_('Trading Pair'), 'trading_pair'),
        AutocompleteFilterFactory(_('Exchange'), 'exchange'),
        'side',
        'is_liquidated',
        'leverage',
        'open_at',
        'close_at',
        'created_at',
        'updated_at',
    )

    autocomplete_fields = ('user', 'trading_pair', 'exchange')
    search_fields = ('user__username', 'trading_pair__symbol', 'exchange__name')

    fieldsets = (
        (_('Basic Info'), {
            'fields': ('user', 'trading_pair', 'exchange', 'side')
        }),
        (_('Prices & Volume'), {
            'fields': (('open_price', 'close_price'),
                       ('volume', 'leverage'))
        }),
        (_('Costs & Funding'), {
            'fields': ('funding', 'fees', 'is_liquidated')
        }),
        (_('Timing'), {
            'fields': (('open_at', 'close_at'),)
        }),
        (_('Calculated Fields'), {
            'fields': (
                'pnl_short',
                'margin_open_short', 'margin_close_short',
                'income_short', 'roi_short', 'roi_percent_short',
                'duration', 'human_duration',
            )
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    actions = ['recalculate_deal', 'delete_unused_items']

    @admin.action(description=_('Recalculate selected deals'))
    def recalculate_deal(self, request, queryset):
        for obj in queryset:
            obj.updated_at = now()
            obj.save()

    @admin.action(description=_('Delete unused items'))
    def delete_unused_items(self, request, queryset):
        used_ids = set(
            ArbitrageDeal.objects.filter(
                Q(short__in=queryset) | Q(long__in=queryset)
            ).values_list('short_id', 'long_id')
        )
        used_ids = {id for pair in used_ids for id in pair if id is not None}

        unused_items = queryset.exclude(id__in=used_ids)
        deleted_count = unused_items.count()

        if deleted_count > 0:
            unused_items.delete()
            self.message_user(request, f'Successfully deleted {deleted_count} unused item(s).')
        else:
            self.message_user(request, 'No unused items found to delete.')


@admin.register(ArbitrageDeal)
class ArbitrageDealAdmin(ImportExportModelAdmin, TotalsumAdmin, admin.ModelAdmin):
    resource_classes = [ArbitrageDealFullResource]

    def exchanges(self, obj):
        return f'{obj.exchanges}'

    exchanges.short_description = _('Exchanges')
    exchanges.admin_order_field = 'exchanges'

    def pnl_short(self, obj):
        return format_number(obj.pnl)

    pnl_short.short_description = _('PnL')
    pnl_short.admin_order_field = 'pnl'

    def income_short(self, obj):
        return format_number(obj.income)

    income_short.short_description = _('Income')
    income_short.admin_order_field = 'income'

    def fees_short(self, obj):
        return format_number(obj.fees)

    fees_short.short_description = _('Fees')
    fees_short.admin_order_field = 'fees'

    def funding_short(self, obj):
        return format_number(obj.funding)

    funding_short.short_description = _('Funding')
    funding_short.admin_order_field = 'funding'

    def roi_short(self, obj):
        return format_number(obj.roi)

    roi_short.short_description = _('ROI')

    def roi_percent_short(self, obj):
        return format_number(obj.roi_percent) + '%'

    roi_percent_short.short_description = _('ROI %')
    roi_percent_short.admin_order_field = 'roi_percent'

    def spread_open_short(self, obj):
        return format_number(obj.spread_open) + '%'

    spread_open_short.short_description = _('Spread Open')

    def spread_close_short(self, obj):
        return format_number(obj.spread_close) + '%'

    spread_close_short.short_description = _('Spread Close')

    def spread_short(self, obj):
        return format_number(obj.spread) + '%'

    spread_short.short_description = _('Spread')
    spread_short.admin_order_field = 'spread'

    def margin_open_short(self, obj):
        return format_number(obj.margin_open)

    margin_open_short.short_description = _('Margin Open')
    margin_open_short.admin_order_field = 'margin_open'

    def margin_close_short(self, obj):
        return format_number(obj.margin_close)

    margin_close_short.short_description = _('Margin Close')

    def trading_volume_short(self, obj):
        return format_number(obj.trading_volume)

    trading_volume_short.short_description = _('Trading Volume')
    trading_volume_short.admin_order_field = 'trading_volume'

    def apr_percent_short(self, obj):
        return format_number(obj.apr_percent) + '%'

    apr_percent_short.short_description = _('APR %')
    apr_percent_short.admin_order_field = 'apr_percent'

    def open_price_short(self, obj):
        if not obj.short:
            return '-'
        return format_number(obj.short.open_price)

    open_price_short.short_description = _('Open Price Short')

    def close_price_short(self, obj):
        if not obj.short:
            return '-'
        return format_number(obj.short.close_price)

    close_price_short.short_description = _('Close Price Short')

    def volume_short(self, obj):
        if not obj.short:
            return '-'
        return format_number(obj.short.volume)

    volume_short.short_description = _('Volume Short')

    def leverage_short(self, obj):
        if not obj.short:
            return '-'
        return format_number(obj.short.leverage)

    leverage_short.short_description = _('Leverage Short')

    def duration_short(self, obj):
        if not obj.short:
            return '-'
        return obj.short.duration

    duration_short.short_description = _('Duration Short')

    def human_duration_short(self, obj):
        if not obj.short:
            return '-'
        return obj.short.human_duration

    human_duration_short.short_description = _('Human Duration Short')

    def pair_short(self, obj):
        if obj.short and obj.short.trading_pair:
            return model_link(obj.short.trading_pair)
        return '-'

    pair_short.short_description = _('Pair Short')

    def open_price_long(self, obj):
        if not obj.long:
            return '-'
        return format_number(obj.long.open_price)

    open_price_long.long_description = _('Open Price Long')

    def close_price_long(self, obj):
        if not obj.long:
            return '-'
        return format_number(obj.long.close_price)

    close_price_long.long_description = _('Close Price Long')

    def volume_long(self, obj):
        if not obj.long:
            return '-'
        return format_number(obj.long.volume)

    volume_long.long_description = _('Volume Long')

    def leverage_long(self, obj):
        if not obj.long:
            return '-'
        return format_number(obj.long.leverage)

    leverage_long.long_description = _('Leverage Long')

    def duration_long(self, obj):
        if not obj.long:
            return '-'
        return obj.long.duration

    duration_long.long_description = _('Duration Long')

    def human_duration_long(self, obj):
        if not obj.long:
            return '-'
        return obj.long.human_duration

    human_duration_long.long_description = _('Human Duration Long')

    def pair_long(self, obj):
        if obj.long and obj.long.trading_pair:
            return model_link(obj.long.trading_pair)
        return '-'

    pair_long.long_description = _('Pair Long')

    list_select_related = (
        'short', 'long', 'short__exchange', 'long__exchange', 'user', 'short__trading_pair', 'long__trading_pair'
    )

    list_filter = (
        AutocompleteFilterFactory(_('User'), 'user'),
        AutocompleteFilterFactory(_('Short'), 'short'),
        AutocompleteFilterFactory(_('Long'), 'long'),
        AutocompleteFilterFactory(_('Short Trading Pair'), 'short__trading_pair'),
        AutocompleteFilterFactory(_('Long Trading Pair'), 'long__trading_pair'),
        AutocompleteFilterFactory(_('Short Exchange'), 'short__exchange'),
        AutocompleteFilterFactory(_('Long Exchange'), 'long__exchange'),
        'type',
        'short__is_liquidated',
        'long__is_liquidated',
        'created_at',
        'updated_at',
    )

    autocomplete_fields = ('user', 'short', 'long')
    search_fields = ('user__username', 'short__exchange__name', 'long__exchange__name')

    list_display = (
        'user', 'pair', 'exchanges',
        'pnl_short', 'income_short', 'roi_percent_short', 'apr_percent_short',
        'spread_short', 'margin_open_short', 'trading_volume_short',
        'fees_short', 'funding_short',
        'duration', 'human_duration',
        'created_at'
    )

    readonly_fields = (
        'pnl_short', 'income_short', 'fees_short', 'funding_short',
        'roi_short', 'roi_percent_short', 'apr_percent_short', 'spread_open_short',
        'spread_close_short', 'spread_short',
        'margin_open_short', 'margin_close_short',
        'trading_volume_short',
        'created_at', 'updated_at',
        'open_price_short', 'close_price_short',
        'volume_short', 'leverage_short',
        'duration_short', 'human_duration_short',
        'open_price_long', 'close_price_long',
        'volume_long', 'leverage_long',
        'duration_long', 'human_duration_long',
        'pair_short', 'pair_long',
        'duration', 'human_duration',
    )

    fieldsets = (
        (_('Deal Owner & Items'), {
            'fields': (
                'user', 'short', 'long', 'type', 'note',
            )
        }),
        (_('Short Position'), {
            'fields': (
                'pair_short',
                'open_price_short', 'close_price_short',
                'volume_short', 'leverage_short',
                'duration_short', 'human_duration_short',
            )
        }),
        (_('Long Position'), {
            'fields': (
                'pair_long',
                'open_price_long', 'close_price_long',
                'volume_long', 'leverage_long',
                'duration_long', 'human_duration_long',
            )
        }),
        (_('Calculated Fields'), {
            'fields': (
                'pnl_short', 'income_short', 'funding_short', 'fees_short',
                'roi_short', 'roi_percent_short', 'apr_percent_short',
                'spread_open_short', 'spread_close_short', 'spread_short',
                'margin_open_short', 'margin_close_short', 'trading_volume_short',
                'duration', 'human_duration',
            )
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


    def get_fieldsets(self, request, obj=None):
        fs = deepcopy(super().get_fieldsets(request, obj) or self.fieldsets)

        if not obj:
            return fs  # на форме создания пока не скрываем

        if obj.type == obj.DealType.TRADE:
            keep_sections = []
            for title, opts in fs:
                if title == _('Long Position') and obj.short and not obj.long:
                    continue
                if title == _('Short Position') and obj.long and not obj.short:
                    continue
                if title == _('Calculated Fields'):
                    fields = list(opts.get('fields', ()))
                    fields = [f for f in fields if f not in (
                        'spread_open_short', 'spread_close_short', 'spread_short'
                    )]
                    opts = {**opts, 'fields': tuple(fields)}
                keep_sections.append((title, opts))
            fs = keep_sections

        return fs

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj) or self.readonly_fields)

        if obj and obj.type == obj.DealType.TRADE:
            for f in ('spread_open_short', 'spread_close_short', 'spread_short'):
                if f in ro:
                    ro.remove(f)
            if obj.short and not obj.long:
                for f in ('open_price_long', 'close_price_long', 'volume_long',
                          'leverage_long', 'duration_long', 'human_duration_long', 'pair_long'):
                    if f in ro:
                        ro.remove(f)
            if obj.long and not obj.short:
                for f in ('open_price_short', 'close_price_short', 'volume_short',
                          'leverage_short', 'duration_short', 'human_duration_short', 'pair_short'):
                    if f in ro:
                        ro.remove(f)

        return tuple(ro)

    totalsum_list = ('pnl', 'income', 'fees', 'funding', 'roi', 'margin_open', 'margin_close', 'trading_volume')

    action_form = UserForm
    actions = ['assign_user', 'recalculate_deal']

    @admin.action(description=_('Assign selected user to a deal'))
    def assign_user(self, request, queryset):
        selected_user = request.POST.get('user_field')
        if selected_user:
            for obj in queryset:
                if selected_user:
                    obj.user_id = selected_user
                    obj.short.user_id = selected_user
                    obj.long.user_id = selected_user
                    obj.save(
                        update_fields=['user_id']
                    )
                    obj.short.save(
                        update_fields=['user_id']
                    )
                    obj.long.save(
                        update_fields=['user_id']
                    )

    @admin.action(description=_('Recalculate selected deals'))
    def recalculate_deal(self, request, queryset):
        for obj in queryset:
            obj.updated_at = now()
            obj.save()
