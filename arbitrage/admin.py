from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from totalsum.admin import TotalsumAdmin

from utils.helpers import trim_trailing_zeros, model_link
from .forms import UserForm, ExchangeCredentialsAdminForm
from .models import Exchange, TradingPair, ArbitrageDealItem, ArbitrageDeal, ExchangeCredentials
from .resources import ArbitrageDealResource, ArbitrageDealItemResource, ArbitrageDealFullResource


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
    list_display = ('name', 'is_enabled')
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
        'is_enabled'
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
    search_fields = ('exchange__name', 'user__username')


@admin.register(TradingPair)
class TradingPairAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('base_currency', 'quote_currency', 'symbol')
    fieldsets = (
        (None, {
            'fields': ('base_currency', 'quote_currency', 'symbol')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'symbol')
    search_fields = ('symbol',)


@admin.register(ArbitrageDealItem)
class ArbitrageDealItemAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = ArbitrageDealItemResource

    def pnl_short(self, obj):
        return trim_trailing_zeros(obj.pnl, 8)

    pnl_short.short_description = _('PnL')

    def income_short(self, obj):
        return trim_trailing_zeros(obj.income, 8)

    income_short.short_description = _('Income')

    def roi_short(self, obj):
        return trim_trailing_zeros(obj.roi, 8)

    roi_short.short_description = _('ROI')

    def roi_percent_short(self, obj):
        return trim_trailing_zeros(obj.roi_percent, 8)

    roi_percent_short.short_description = _('ROI %')

    def margin_open_short(self, obj):
        return trim_trailing_zeros(obj.margin_open, 8)

    margin_open_short.short_description = _('Margin Open')

    def margin_close_short(self, obj):
        return trim_trailing_zeros(obj.margin_close, 8)

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


@admin.register(ArbitrageDeal)
class ArbitrageDealAdmin(ImportExportModelAdmin, TotalsumAdmin, admin.ModelAdmin):
    resource_classes = [ArbitrageDealResource, ArbitrageDealFullResource]

    def exchanges(self, obj):
        return f'{obj.exchanges}'

    exchanges.short_description = _('Exchanges')

    def pnl_short(self, obj):
        return trim_trailing_zeros(obj.pnl, 8)

    pnl_short.short_description = _('PnL')

    def income_short(self, obj):
        return trim_trailing_zeros(obj.income, 8)

    income_short.short_description = _('Income')

    def fees_short(self, obj):
        return trim_trailing_zeros(obj.fees, 8)

    fees_short.short_description = _('Fees')

    def funding_short(self, obj):
        return trim_trailing_zeros(obj.funding, 8)

    funding_short.short_description = _('Funding')

    def roi_short(self, obj):
        return trim_trailing_zeros(obj.roi, 8)

    roi_short.short_description = _('ROI')

    def roi_percent_short(self, obj):
        return trim_trailing_zeros(obj.roi_percent, 8) + '%'

    roi_percent_short.short_description = _('ROI %')

    def spread_open_short(self, obj):
        return trim_trailing_zeros(obj.spread_open, 8) + '%'

    spread_open_short.short_description = _('Spread Open')

    def spread_close_short(self, obj):
        return trim_trailing_zeros(obj.spread_close, 8) + '%'

    spread_close_short.short_description = _('Spread Close')

    def spread_short(self, obj):
        return trim_trailing_zeros(obj.spread, 8) + '%'

    spread_short.short_description = _('Spread')

    def margin_open_short(self, obj):
        return trim_trailing_zeros(obj.margin_open, 8)

    margin_open_short.short_description = _('Margin Open')

    def margin_close_short(self, obj):
        return trim_trailing_zeros(obj.margin_close, 8)

    margin_close_short.short_description = _('Margin Close')

    def trading_volume_short(self, obj):
        return trim_trailing_zeros(obj.trading_volume, 8)

    trading_volume_short.short_description = _('Trading Volume')

    def open_price_short(self, obj):
        if not obj.short:
            return '-'
        return trim_trailing_zeros(obj.short.open_price, 8)

    open_price_short.short_description = _('Open Price Short')

    def close_price_short(self, obj):
        if not obj.short:
            return '-'
        return trim_trailing_zeros(obj.short.close_price, 8)

    close_price_short.short_description = _('Close Price Short')

    def volume_short(self, obj):
        if not obj.short:
            return '-'
        return trim_trailing_zeros(obj.short.volume, 8)

    volume_short.short_description = _('Volume Short')

    def leverage_short(self, obj):
        if not obj.short:
            return '-'
        return trim_trailing_zeros(obj.short.leverage, 8)

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
        return trim_trailing_zeros(obj.long.open_price, 8)

    open_price_long.long_description = _('Open Price Long')

    def close_price_long(self, obj):
        if not obj.long:
            return '-'
        return trim_trailing_zeros(obj.long.close_price, 8)

    close_price_long.long_description = _('Close Price Long')

    def volume_long(self, obj):
        if not obj.long:
            return '-'
        return trim_trailing_zeros(obj.long.volume, 8)

    volume_long.long_description = _('Volume Long')

    def leverage_long(self, obj):
        if not obj.long:
            return '-'
        return trim_trailing_zeros(obj.long.leverage, 8)

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
        'created_at',
        'updated_at',
    )

    autocomplete_fields = ('user', 'short', 'long')
    search_fields = ('user__username', 'short__exchange__name', 'long__exchange__name')

    list_display = (
        'exchanges', 'pair', 'user', 'pnl_short', 'income_short', 'fees_short', 'funding_short',
        'roi_percent_short', 'spread_open_short', 'spread_close_short', 'spread_short',
        'margin_open_short', 'margin_close_short', 'trading_volume_short',
        'duration', 'human_duration',
        'created_at', 'updated_at'
    )

    readonly_fields = (
        'pnl_short', 'income_short', 'fees_short', 'funding_short',
        'roi_short', 'roi_percent_short', 'spread_open_short',
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
                'user', 'short', 'long', 'note',
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
                'roi_short', 'roi_percent_short',
                'spread_open_short', 'spread_close_short', 'spread_short',
                'margin_open_short', 'margin_close_short', 'trading_volume_short',
                'duration', 'human_duration',
            )
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    totalsum_list = ('pnl', 'income', 'fees', 'funding', 'roi', 'margin_open', 'margin_close', 'trading_volume')

    action_form = UserForm
    actions = ['assign_user']

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
