from django.contrib import admin

from .models import Exchange, TradingPair, ArbitrageDealItem, ArbitrageDeal, ExchangeCredentials


class ExchangeCredentialsInline(admin.TabularInline):
    model = ExchangeCredentials
    extra = 0
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'api_key',
                'api_secret',
                'is_enabled',
            )
        }),
    )


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_enabled')
    fieldsets = (
        (None, {
            'fields': ('name', 'is_enabled')
        }),
    )
    inlines = [ExchangeCredentialsInline]


@admin.register(ExchangeCredentials)
class ExchangeCredentialsAdmin(admin.ModelAdmin):
    list_display = ('exchange', 'user', 'api_key', 'api_secret', 'is_enabled')
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
    )


@admin.register(TradingPair)
class TradingPairAdmin(admin.ModelAdmin):
    list_display = ('base_currency', 'quote_currency', 'symbol')
    fieldsets = (
        (None, {
            'fields': ('base_currency', 'quote_currency')
        }),
    )


@admin.register(ArbitrageDealItem)
class ArbitrageDealItemAdmin(admin.ModelAdmin):
    list_display = (
        'trading_pair', 'exchange', 'side', 'open_price', 'close_price',
        'volume', 'leverage', 'fees', 'funding', 'is_liquidated',
        'pnl', 'income', 'roi_percent', 'duration', 'human_duration'
    )
    readonly_fields = (
        'pnl', 'margin_open', 'margin_close', 'income',
        'roi', 'roi_percent', 'duration', 'human_duration', 'created_at', 'updated_at',
    )
    fieldsets = (
        ('Basic Info', {
            'fields': (
                'trading_pair', 'exchange', 'side',
            )
        }),
        ('Prices & Volume', {
            'fields': (
                ('open_price', 'close_price'),
                ('volume', 'leverage'),
            )
        }),
        ('Costs & Funding', {
            'fields': (
                'fees', 'funding', 'is_liquidated',
            )
        }),
        ('Timing', {
            'fields': (
                ('open_at', 'close_at'),
            )
        }),
        ('Calculated Fields', {
            'fields': (
                'pnl', 'margin_open', 'margin_close', 'income',
                'roi', 'roi_percent', 'duration', 'human_duration'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ArbitrageDeal)
class ArbitrageDealAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'pnl', 'income', 'fees', 'funding', 'roi_percent',
        'spread_open', 'spread_close', 'spread',
        'margin_open', 'margin_close', 'trading_volume',
        'created_at', 'updated_at'
    )
    readonly_fields = (
        'pnl', 'income', 'fees', 'funding', 'roi',
        'roi_percent', 'spread_open', 'spread_close', 'spread',
        'margin_open', 'margin_close', 'trading_volume',
        'created_at', 'updated_at'
    )
    fieldsets = (
        ('Deal Owner & Items', {
            'fields': (
                'user', 'short', 'long', 'note',
            )
        }),
        ('Calculated Fields', {
            'fields': (
                'pnl', 'income', 'fees', 'funding',
                'roi', 'roi_percent',
                'spread_open', 'spread_close', 'spread',
                'margin_open', 'margin_close', 'trading_volume',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
