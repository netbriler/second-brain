from decimal import Decimal

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

    symbol = models.CharField(
        max_length=20,
        verbose_name=_('Symbol'),
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    def save(self, *args, **kwargs):
        self.symbol = f'{self.base_currency}/{self.quote_currency}' if self.base_currency and self.quote_currency else ''
        super().save(*args, **kwargs)

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
        null=True,
        blank=True,
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

    # New fields that used to be properties
    pnl = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('PnL')
    )
    margin_open = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Margin Open')
    )
    margin_close = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Margin Close')
    )
    income = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Income')
    )
    roi = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('ROI')
    )
    roi_percent = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('ROI %')
    )
    duration = models.DurationField(
        blank=True, null=True,
        verbose_name=_('Duration'),
    )
    human_duration = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Human Duration'),
    )

    def save(self, *args, **kwargs):
        # Calculate PnL
        if self.open_price and self.close_price:
            if self.side in ('short', 'margin-short'):
                self.pnl = (self.open_price - self.close_price) * self.volume
            else:
                self.pnl = (self.close_price - self.open_price) * self.volume

        # Margin calculations
        if self.open_price and self.volume:
            self.margin_open = (self.open_price * self.volume / self.leverage)
        if self.close_price and self.volume:
            self.margin_close = (self.close_price * self.volume / self.leverage)

        # Income includes PnL + fees + funding
        self.income = self.pnl
        if self.fees:
            self.income += self.fees
        if self.funding:
            self.income += self.funding

        # ROI based on margin_open
        if self.margin_open != 0:
            self.roi = self.pnl / self.margin_open
        else:
            self.roi = Decimal('0.0')

        # ROI in percent
        self.roi_percent = round(self.roi * Decimal('100.0'), 2)

        # Duration
        if self.open_at and self.close_at:
            self.duration = self.close_at - self.open_at

            # Human duration
            self.human_duration = timesince(self.open_at, self.close_at)
        elif self.open_at and not self.close_at:
            self.duration = None
            self.human_duration = timesince(self.open_at)
        elif self.close_at and not self.open_at:
            self.duration = None
            self.human_duration = timesince(self.close_at)
        else:
            self.duration = None
            self.human_duration = None

        super().save(*args, **kwargs)

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
        null=True,
        blank=True,
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

    exchanges = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name=_('Exchanges'),
    )

    @property
    def pair(self):
        if not self.short.trading_pair or not self.long.trading_pair:
            return '-'
        if self.short.trading_pair == self.long.trading_pair:
            return self.short.trading_pair

        return f'{self.short.trading_pair} > {self.long.trading_pair}'

    # Storing numeric values
    pnl = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('PnL'),
    )
    income = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Income'),
    )
    fees = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Fees'),
    )
    funding = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Funding'),
    )
    roi = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('ROI'),
    )
    roi_percent = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('ROI Percent'),
    )
    spread_open = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Spread Open (%)'),
    )
    spread_close = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Spread Close (%)'),
    )
    spread = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Spread (%)'),
    )
    margin_open = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Margin Open'),
    )
    margin_close = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Margin Close'),
    )
    trading_volume = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Trading Volume'),
    )

    def save(self, *args, **kwargs):
        """
        Compute and store cumulative fields whenever the ArbitrageDeal is saved.
        """
        # Safety check: if related items are missing for some reason, bail early.
        if not self.short_id or not self.long_id:
            super().save(*args, **kwargs)
            return

        # Exchanges
        self.exchanges = f'{self.short.exchange} - {self.long.exchange}'

        # PnL, Income, Fees, Funding
        self.pnl = self.short.pnl + self.long.pnl
        self.income = self.short.income + self.long.income
        self.fees = self.short.fees + self.long.fees
        self.funding = self.short.funding + self.long.funding

        # Margin
        total_margin_open = self.short.margin_open + self.long.margin_open
        self.margin_open = total_margin_open
        self.margin_close = self.short.margin_close + self.long.margin_close

        # ROI
        if total_margin_open:
            self.roi = self.pnl / total_margin_open
        else:
            self.roi = Decimal('0.0')

        self.roi_percent = self.roi * Decimal('100.0')

        # Spread
        # Be mindful of divide-by-zero scenarios
        if self.long.open_price and self.short.open_price:
            self.spread_open = ((self.short.open_price / self.long.open_price) - 1) * Decimal('100.0')
        else:
            self.spread_open = Decimal('0.0')

        if self.long.close_price and self.short.close_price:
            self.spread_close = ((self.short.close_price / self.long.close_price) - 1) * Decimal('100.0')
        else:
            self.spread_close = Decimal('0.0')

        self.spread = self.spread_open - self.spread_close

        # Trading volume
        # (short.margin_open + long.margin_open) * short.leverage
        # + (short.margin_close + long.margin_close) * long.leverage
        self.trading_volume = (
                (self.short.margin_open + self.long.margin_open) * Decimal(self.short.leverage) +
                (self.short.margin_close + self.long.margin_close) * Decimal(self.long.leverage)
        )

        # Round numeric fields
        self.spread_open = self.spread_open.quantize(Decimal('0.01'))
        self.spread_close = self.spread_close.quantize(Decimal('0.01'))
        self.spread = self.spread.quantize(Decimal('0.01'))
        self.roi_percent = self.roi_percent.quantize(Decimal('0.01'))

        super().save(*args, **kwargs)

        if self.user != self.short.user:
            self.short.user = self.user
            self.short.save(
                update_fields=[
                    'user',
                ],
            )

        if self.user != self.long.user:
            self.long.user = self.user
            self.long.save(
                update_fields=[
                    'user',
                ],
            )

    def __str__(self):
        return (
            f'{self.pair} {self.short.exchange} '
            f'> {self.long.exchange} | income: {self.income}'
        )
