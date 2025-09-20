import base64
import hashlib
from decimal import Decimal

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timesince import timesince
from django.utils.timezone import now
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
        key = base64.urlsafe_b64encode(
            hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
        )
        f = Fernet(key)
        return f.decrypt(self._api_secret.encode()).decode()

    @api_secret.setter
    def api_secret(self, value):
        key = base64.urlsafe_b64encode(
            hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
        )
        f = Fernet(key)
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
        max_digits=20,
        decimal_places=8,
        verbose_name=_('Open Price'),
    )

    close_price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name=_('Close Price'),
    )

    volume = models.DecimalField(
        max_digits=20,
        default=Decimal('0.0'),
        decimal_places=8,
        verbose_name=_('Volume'),
    )

    leverage = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Leverage'),
        validators=[MinValueValidator(1)],
    )

    fees = models.DecimalField(
        max_digits=20,
        default=Decimal('0.0'),
        decimal_places=8,
        verbose_name=_('Fees'),
    )

    funding = models.DecimalField(
        max_digits=20,
        default=Decimal('0.0'),
        decimal_places=8,
        verbose_name=_('Funding'),
    )

    is_liquidated = models.BooleanField(
        default=False,
        verbose_name=_('Is Liquidated'),
    )

    open_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Open At'),
    )

    close_at = models.DateTimeField(
        blank=True,
        null=True,
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
        max_digits=20,
        decimal_places=8,
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
        self.pnl = Decimal('0.0')
        if self.close_price is not None:
            if self.side in ('short', 'margin-short'):
                self.pnl = (self.open_price - self.close_price) * self.volume
            else:
                self.pnl = (self.close_price - self.open_price) * self.volume

        self.income = self.pnl
        if self.fees:
            self.income += self.fees
        if self.funding:
            self.income += self.funding

        self.margin_open = (self.open_price * self.volume / self.leverage)
        if self.close_price is not None:
            self.margin_close = (self.close_price * self.volume / self.leverage) + self.income

        if self.margin_open != 0:
            self.roi = self.income / self.margin_open
        else:
            self.roi = Decimal('0.0')
        self.roi_percent = round(self.roi * Decimal('100.0'), 2)

        if self.open_at and self.close_at:
            self.duration = self.close_at - self.open_at
            self.human_duration = timesince(self.open_at, self.close_at)
        else:
            self.duration = None
            self.human_duration = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.trading_pair.symbol} - {self.exchange.name} - {self.side} | {self.open_price} - {self.close_price}'


class ArbitrageDeal(models.Model):
    class DealType(models.TextChoices):
        ARBITRAGE = 'arbitrage', _('Arbitrage')
        TRADE = 'trade', _('Trade')

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

    type = models.CharField(
        max_length=20,
        choices=DealType.choices,
        default=DealType.ARBITRAGE,
        verbose_name=_('Deal Type'),
    )

    short = models.ForeignKey(
        ArbitrageDealItem,
        related_name='short_deal',
        on_delete=models.CASCADE,
        verbose_name=_('Short Deal'),
        null=True,
        blank=True,
    )

    long = models.ForeignKey(
        ArbitrageDealItem,
        related_name='long_deal',
        on_delete=models.CASCADE,
        verbose_name=_('Long Deal'),
        null=True,
        blank=True,
    )

    note = models.TextField(
        blank=True,
        null=True,
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
        if self.type == self.DealType.TRADE:
            if self.short:
                return self.short.trading_pair
            elif self.long:
                return self.long.trading_pair
            return '-'

        if not self.short or not self.long:
            return '-'
        if not self.short.trading_pair or not self.long.trading_pair:
            return '-'
        if self.short.trading_pair == self.long.trading_pair:
            return self.short.trading_pair

        return f'{self.short.trading_pair} > {self.long.trading_pair}'

    # Storing numeric values
    pnl = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('PnL'),
    )

    income = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Income'),
    )

    fees = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Fees'),
    )

    funding = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Funding'),
    )

    roi = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('ROI'),
    )

    roi_percent = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('ROI Percent'),
    )

    spread_open = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Spread Open (%)'),
    )

    spread_close = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Spread Close (%)'),
    )

    spread = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Spread (%)'),
    )

    margin_open = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Margin Open'),
    )

    margin_close = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Margin Close'),
    )

    trading_volume = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Trading Volume'),
    )

    duration = models.DurationField(
        blank=True,
        null=True,
        verbose_name=_('Duration'),
    )

    human_duration = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Human Duration'),
    )

    apr_percent = models.DecimalField(
        max_digits=20, decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('APR %'),
    )

    def clean(self):
        super().clean()
        if self.type == self.DealType.ARBITRAGE:
            if not self.short or not self.long:
                raise ValidationError(
                    _('Arbitrage deals must have both short and long positions.')
                )
        elif self.type == self.DealType.TRADE:
            if not self.short and not self.long:
                raise ValidationError(
                    _('Trade deals must have either short or long position.')
                )
            if self.short and self.long:
                raise ValidationError(
                    _('Trade deals must have only one position (either short or long).')
                )

    def save(self, *args, **kwargs):
        self.full_clean()

        # Handle different deal types
        if self.type == self.DealType.ARBITRAGE:
            if not self.short_id or not self.long_id:
                super().save(*args, **kwargs)
                return
            self.exchanges = f'{self.short.exchange} - {self.long.exchange}' if self.short.exchange != self.long.exchange else f'{self.short.exchange}'

            self.pnl = self.short.pnl + self.long.pnl
            self.income = self.short.income + self.long.income
            self.fees = self.short.fees + self.long.fees
            self.funding = self.short.funding + self.long.funding

            total_margin_open = self.short.margin_open + self.long.margin_open
            self.margin_open = total_margin_open
            self.margin_close = self.short.margin_close + self.long.margin_close
        elif self.type == self.DealType.TRADE:
            if not self.short_id and not self.long_id:
                super().save(*args, **kwargs)
                return

            # Use the single position for trade deals
            position = self.short if self.short else self.long
            self.exchanges = position.exchange.name

            # Single position values
            self.pnl = position.pnl
            self.income = position.income
            self.fees = position.fees
            self.funding = position.funding
            self.margin_open = position.margin_open
            self.margin_close = position.margin_close
            total_margin_open = position.margin_open
        else:
            super().save(*args, **kwargs)
            return

        if total_margin_open:
            self.roi = self.income / total_margin_open
        else:
            self.roi = Decimal('0.0')

        self.roi_percent = self.roi * Decimal('100.0')

        if self.type == self.DealType.ARBITRAGE and self.short and self.long:
            if self.long.open_price and self.short.open_price:
                self.spread_open = ((self.short.open_price / self.long.open_price) - 1) * Decimal('100.0')
            else:
                self.spread_open = Decimal('0.0')

            if self.long.close_price and self.short.close_price:
                self.spread_close = ((self.short.close_price / self.long.close_price) - 1) * Decimal('100.0')
            else:
                self.spread_close = Decimal('0.0')

            self.spread = self.spread_open - self.spread_close

            self.trading_volume = (
                    (self.short.margin_open + self.long.margin_open) * Decimal(self.short.leverage) +
                    (self.short.margin_close + self.long.margin_close) * Decimal(self.long.leverage)
            )
        else:
            self.spread_open = Decimal('0.0')
            self.spread_close = Decimal('0.0')
            self.spread = Decimal('0.0')

            position = self.short if self.short else self.long
            if position:
                self.trading_volume = (
                        position.margin_open * Decimal(position.leverage) +
                        position.margin_close * Decimal(position.leverage)
                )
            else:
                self.trading_volume = Decimal('0.0')

        self.spread_open = self.spread_open.quantize(Decimal('0.01'))
        self.spread_close = self.spread_close.quantize(Decimal('0.01'))
        self.spread = self.spread.quantize(Decimal('0.01'))
        self.roi_percent = self.roi_percent.quantize(Decimal('0.01'))

        if self.type == self.DealType.ARBITRAGE and self.short and self.long:
            if self.short.open_at and self.long.open_at and self.short.close_at and self.long.close_at:
                self.duration = max(
                    self.short.close_at, self.long.close_at
                ) - min(
                    self.short.open_at, self.long.open_at
                )

                self.human_duration = timesince(
                    min(self.short.open_at, self.long.open_at),
                    max(self.short.close_at, self.long.close_at),
                )
        else:
            position = self.short if self.short else self.long
            if position and position.open_at and position.close_at:
                self.duration = position.close_at - position.open_at
                self.human_duration = timesince(position.open_at, position.close_at)
            else:
                self.duration = None
                self.human_duration = None

        if self.duration and total_margin_open and self.duration.total_seconds() > 0:
            # APR = (income / margin_open) * (365.25 days / duration) * 100
            duration_days = Decimal(str(self.duration.total_seconds() / 86400))
            if duration_days > 0:
                self.apr_percent = (self.income / total_margin_open) * (Decimal('365.25') / duration_days) * Decimal(
                    '100.0'
                )
            else:
                self.apr_percent = Decimal('0.0')
        else:
            self.apr_percent = Decimal('0.0')

        self.apr_percent = self.apr_percent.quantize(Decimal('0.01'))

        super().save(*args, **kwargs)

        if self.short and self.user != self.short.user:
            self.short.user = self.user
            self.short.save(
                update_fields=[
                    'user',
                ],
            )

        if self.long and self.user != self.long.user:
            self.long.user = self.user
            self.long.save(
                update_fields=[
                    'user',
                ],
            )

    def __str__(self):
        if self.type == self.DealType.TRADE:
            position = self.short if self.short else self.long
            if position:
                return f'{self.pair} {position.exchange} | income: {self.income}'
            return f'Trade Deal | income: {self.income}'

        if self.short and self.long:
            return (
                f'{self.pair} {self.short.exchange} '
                f'> {self.long.exchange} | income: {self.income}'
            )
        return f'Arbitrage Deal | income: {self.income}'


class Balance(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    account = models.CharField(max_length=50)
    asset = models.CharField(max_length=50)
    free = models.DecimalField(max_digits=20, decimal_places=8)
    locked = models.DecimalField(max_digits=20, decimal_places=8)

    def __str__(self):
        return f"{self.exchange.name} - {self.asset}"


class BalanceSnapshot(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    account = models.CharField(max_length=50)
    asset = models.CharField(max_length=50)
    free_snapshot = models.DecimalField(max_digits=20, decimal_places=8)
    locked_snapshot = models.DecimalField(max_digits=20, decimal_places=8)
    snapshot_time = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.exchange.name} - {self.asset} - {self.snapshot_time}"
