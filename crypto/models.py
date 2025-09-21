import base64
import hashlib
from decimal import Decimal

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from crypto.services.crypto_service import CryptoService


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
        related_name='crypto_exchanges',
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


class CryptoDealItem(models.Model):
    class Meta:
        verbose_name = _('Crypto Deal Item')
        verbose_name_plural = _('Crypto Deal Items')

    user = models.ForeignKey(
        'users.User',
        related_name='crypto_deals_items',
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
        related_name='crypto_deal',
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

    extra_margin = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Extra Margin'),
    )

    margin_open = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Margin Open')
    )

    margin_close = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Margin Close')
    )

    trading_volume = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Trading Volume'),
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

    def save(self, apply_item: bool = True, *args, **kwargs):
        if apply_item:
            CryptoService.apply_item(self)

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.trading_pair.symbol} - {self.exchange.name} - {self.side} | {self.open_price} - {self.close_price}'


class CryptoDeal(models.Model):
    class DealType(models.TextChoices):
        ARBITRAGE = 'arbitrage', _('Arbitrage')
        HEDGE = 'hedge', _('Hedge')
        TRADE = 'trade', _('Trade')

    class Meta:
        verbose_name = _('Crypto Deal')
        verbose_name_plural = _('Crypto Deals')

    user = models.ForeignKey(
        'users.User',
        related_name='crypto_deals',
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
        CryptoDealItem,
        related_name='short_deal',
        on_delete=models.CASCADE,
        verbose_name=_('Short Deal'),
        null=True,
        blank=True,
    )

    long = models.ForeignKey(
        CryptoDealItem,
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
        if self.type in [self.DealType.ARBITRAGE, self.DealType.HEDGE]:
            if not self.short or not self.long:
                raise ValidationError(
                    _('Crypto deals must have both short and long positions.')
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

        CryptoService.apply_deal(self)

        super().save(*args, **kwargs)

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
        return f'Crypto Deal | income: {self.income}'


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
