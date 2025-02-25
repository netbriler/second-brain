from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _

from utils.helpers import trim_trailing_zeros


class Exchange(models.Model):
    class Meta:
        verbose_name = _('Exchange')
        verbose_name_plural = _('Exchanges')

    name = models.CharField(max_length=100, unique=True)

    is_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    def __str__(self):
        return self.name


class ExchangeCredentials(models.Model):
    class Meta:
        verbose_name = _('Exchange Credentials')
        verbose_name_plural = _('Exchange Credentials')

    exchange = models.ForeignKey(
        Exchange,
        related_name='credentials',
        on_delete=models.CASCADE,
        verbose_name=_('Exchange'),
    )

    user = models.ForeignKey(
        'users.User',
        related_name='arbitrage_exchanges',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('User'),
    )

    api_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('API Key'),
    )

    _api_secret = models.TextField(blank=True, null=True)

    is_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Is Enabled'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    @property
    def api_secret(self):
        if not self._api_secret:
            return None
        f = Fernet(settings.SECRET_KEY)
        return f.decrypt(self._api_secret.encode()).decode()

    @api_secret.setter
    def api_secret(self, value):
        f = Fernet(settings.SECRET_KEY)
        self._api_secret = f.encrypt(value.encode()).decode()


class TradingPair(models.Model):
    class Meta:
        verbose_name = _('Trading Pair')
        verbose_name_plural = _('Trading Pairs')

    base_currency = models.CharField(
        max_length=10,
        verbose_name=_('Base Currency'),
    )
    quote_currency = models.CharField(
        max_length=10,
        verbose_name=_('Quote Currency'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    @property
    def symbol(self):
        return f'{self.base_currency}/{self.quote_currency}'

    def __str__(self):
        return f'{self.symbol}'


class ArbitrageDealItem(models.Model):
    class Meta:
        verbose_name = _('Arbitrage Deal Item')
        verbose_name_plural = _('Arbitrage Deal Items')

    user = models.ForeignKey(
        'users.User',
        related_name='arbitrage_deals_items',
        on_delete=models.CASCADE,
        verbose_name=_('User'),
    )

    trading_pair = models.ForeignKey(
        TradingPair,
        on_delete=models.CASCADE,
        verbose_name=_('Trading Pair'),
    )

    exchange = models.ForeignKey(
        Exchange,
        related_name='arbitrage_deal',
        on_delete=models.CASCADE,
        verbose_name=_('Exchange'),
    )

    side = models.CharField(
        choices=[
            ('short', _('Short')),
            ('long', _('Long')),
            ('spot', _('Spot')),
            ('margin-short', _('Margin Short')),
            ('margin-long', _('Margin Long')),
        ],
        verbose_name=_('Side'),
    )

    open_price = models.DecimalField(
        max_digits=20, decimal_places=8,
        verbose_name=_('Open Price'),
    )

    close_price = models.DecimalField(
        max_digits=20, decimal_places=8,
        verbose_name=_('Close Price'),
    )

    volume = models.DecimalField(
        max_digits=20, decimal_places=8,
        verbose_name=_('Volume'),
    )

    leverage = models.IntegerField(
        default=1,
        verbose_name=_('Leverage'),
    )

    fees = models.DecimalField(
        max_digits=20, decimal_places=8,
        verbose_name=_('Fees'),
    )

    funding = models.DecimalField(
        max_digits=20, decimal_places=8,
        verbose_name=_('Funding'),
    )

    is_liquidated = models.BooleanField(
        default=False,
        verbose_name=_('Is Liquidated'),
    )

    open_at = models.DateTimeField(
        blank=True, null=True,
        verbose_name=_('Open At'),
    )

    close_at = models.DateTimeField(
        blank=True, null=True,
        verbose_name=_('Close At'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    trades = models.JSONField(
        blank=True, null=True,
        verbose_name=_('Trades')
    )

    @property
    def pnl(self):
        if not self.open_price or not self.close_price:
            return 0
        if self.side in ('short', 'margin-short'):
            return (self.open_price - self.close_price) * self.volume
        elif self.side in ('spot', 'long', 'margin-long'):
            return (self.close_price - self.open_price) * self.volume
        return 0

    @property
    def margin_open(self):
        if not self.open_price or not self.volume:
            return 0
        return self.open_price * self.volume / self.leverage

    @property
    def margin_close(self):
        if not self.close_price or not self.volume:
            return 0
        return self.close_price * self.volume / self.leverage

    @property
    def income(self):
        income = self.pnl
        if self.fees:
            income += self.fees
        if self.funding:
            income += self.funding

        return income

    @property
    def roi(self):
        if not self.margin_open:
            return 0

        return self.pnl / self.margin_open

    @property
    def roi_percent(self):
        return round(self.roi * 100, 2)

    @property
    def duration(self):
        if not self.close_at or not self.open_at:
            return None
        return self.close_at - self.open_at

    @property
    def human_duration(self):
        """ Human-readable string (e.g., '2 days, 3 hours'). """
        if not self.close_at and not self.open_at:
            return None
        if not self.close_at:
            return timesince(self.open_at)
        if not self.open_at:
            return timesince(self.close_at)

        return timesince(self.open_at, self.close_at)

    def __str__(self):
        return f'{self.trading_pair.symbol} - {self.exchange.name} - {self.side} | {self.open_price} - {self.close_price}'


class ArbitrageDeal(models.Model):
    class Meta:
        verbose_name = _('Arbitrage Deal')
        verbose_name_plural = _('Arbitrage Deals')

    user = models.ForeignKey(
        'users.User',
        related_name='arbitrage_deals',
        on_delete=models.CASCADE,
        verbose_name=_('User'),
    )

    short = models.ForeignKey(
        ArbitrageDealItem,
        related_name='short_deal',
        on_delete=models.CASCADE,
        verbose_name=_('Short Deal'),
    )

    long = models.ForeignKey(
        ArbitrageDealItem,
        related_name='long_deal',
        on_delete=models.CASCADE,
        verbose_name=_('Long Deal'),
    )

    note = models.TextField(
        blank=True, null=True,
        verbose_name=_('Note'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    @property
    def exchanges(self):
        return f'{self.short.exchange} - {self.long.exchange}'

    @property
    def pnl(self):
        return self.short.pnl + self.long.pnl

    @property
    def income(self):
        return self.short.income + self.long.income

    @property
    def fees(self):
        return self.short.fees + self.long.fees

    @property
    def funding(self):
        return self.short.funding + self.long.funding

    @property
    def roi(self):
        return self.pnl / (self.short.margin_open + self.long.margin_open)

    @property
    def roi_percent(self):
        return round(self.roi * 100, 2)

    @property
    def spread_open(self):
        return round((self.short.open_price / self.long.open_price - 1) * 100, 2)

    @property
    def spread_close(self):
        return round((self.short.close_price / self.long.close_price - 1) * 100, 2)

    @property
    def spread(self):
        return self.spread_open - self.spread_close

    @property
    def margin_open(self):
        return self.short.margin_open + self.long.margin_open

    @property
    def margin_close(self):
        return self.short.margin_close + self.long.margin_close

    @property
    def trading_volume(self):
        return (self.short.margin_open + self.long.margin_open) * self.short.leverage + (
                self.short.margin_close + self.long.margin_close) * self.long.leverage

    @property
    def pair(self):
        if not self.short.trading_pair or not self.long.trading_pair:
            return '-'
        if self.short.trading_pair == self.long.trading_pair:
            return self.short.trading_pair

        return f'{self.short.trading_pair} > {self.long.trading_pair}'

    def __str__(self):
        return f'{self.short.trading_pair} {self.short.exchange} > {self.long.exchange} | income: {trim_trailing_zeros(self.income, 8)}'
