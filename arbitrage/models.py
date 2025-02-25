from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _


class Exchange(models.Model):
    class Meta:
        verbose_name = _('Exchange')
        verbose_name_plural = _('Exchanges')

    name = models.CharField(max_length=100, unique=True)

    is_enabled = models.BooleanField(default=True)

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

    api_key = models.CharField(max_length=255, blank=True, null=True)

    _api_secret = models.TextField(blank=True, null=True)

    is_enabled = models.BooleanField(default=True)

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

    base_currency = models.CharField(max_length=10)
    quote_currency = models.CharField(max_length=10)

    @property
    def symbol(self):
        return f"{self.base_currency}/{self.quote_currency}"

    def __str__(self):
        return f"{self.base_currency}/{self.quote_currency}"


class ArbitrageDealItem(models.Model):
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE)

    exchange = models.ForeignKey(
        Exchange, related_name='arbitrage_deal', on_delete=models.CASCADE
    )

    side = models.CharField(
        choices=[
            ('short', _('Short')),
            ('long', _('Long')),
            ('spot', _('Spot')),
            ('margin-short', _('Margin Short')),
            ('margin-long', _('Margin Long')),
        ]
    )

    open_price = models.DecimalField(max_digits=20, decimal_places=8)

    close_price = models.DecimalField(max_digits=20, decimal_places=8)

    volume = models.DecimalField(max_digits=20, decimal_places=8)

    leverage = models.IntegerField(default=1)

    fees = models.DecimalField(max_digits=20, decimal_places=8)

    funding = models.DecimalField(max_digits=20, decimal_places=8)

    is_liquidated = models.BooleanField(default=False)

    open_at = models.DateTimeField(
        blank=True, null=True
    )

    close_at = models.DateTimeField(
        blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    trades = models.JSONField(blank=True, null=True)

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
        return self.roi * 100

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
        return f'{self.trading_pair.symbol} - {self.exchange.name} - {self.side} - pnl: {self.pnl}'


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

    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

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
        return self.roi * 100

    @property
    def spread_open(self):
        return (self.short.open_price / self.long.open_price - 1) * 100

    @property
    def spread_close(self):
        return (self.short.close_price / self.long.close_price - 1) * 100

    @property
    def spread(self):
        return self.spread_close - self.spread_open

    @property
    def margin_open(self):
        return self.short.margin_open + self.long.margin_open

    @property
    def margin_close(self):
        return self.short.margin_close + self.long.margin_close

    @property
    def trading_volume(self):
        return self.short.margin_open + self.long.margin_open + self.short.margin_close + self.long.margin_close

    def __str__(self):
        return f'{self.user} - {self.created_at} - {self.updated_at}'
