from decimal import Decimal

from django.db import transaction
from django.utils.dateparse import parse_datetime
from import_export import resources, fields
from import_export.results import Error
from import_export.widgets import ForeignKeyWidget

from .models import (
    CryptoDeal,
    CryptoDealItem,
    TradingPair,
    Exchange,
)


class CryptoDealFullResource(resources.ModelResource):
    """
    A resource for importing/exporting CryptoDeal and its related
    short/long CryptoDealItem. We also handle creation of TradingPair
    and Exchange if they do not exist on import.
    """

    # Short fields
    short_exchange = fields.Field(attribute='short.exchange.name', column_name='short_exchange')
    short_symbol = fields.Field(attribute='short.trading_pair.symbol', column_name='short_symbol')
    short_side = fields.Field(attribute='short.side', column_name='short_side')
    short_open_price = fields.Field(attribute='short.open_price', column_name='short_open_price')
    short_close_price = fields.Field(attribute='short.close_price', column_name='short_close_price')
    short_volume = fields.Field(attribute='short.volume', column_name='short_volume')
    short_leverage = fields.Field(attribute='short.leverage', column_name='short_leverage')
    short_fees = fields.Field(attribute='short.fees', column_name='short_fees')
    short_funding = fields.Field(attribute='short.funding', column_name='short_funding')
    short_is_liquidated = fields.Field(attribute='short.is_liquidated', column_name='short_is_liquidated')
    short_open_at = fields.Field(attribute='short.open_at', column_name='short_open_at')
    short_close_at = fields.Field(attribute='short.close_at', column_name='short_close_at')

    # Long fields
    long_exchange = fields.Field(attribute='long.exchange.name', column_name='long_exchange')
    long_symbol = fields.Field(attribute='long.trading_pair.symbol', column_name='long_symbol')
    long_side = fields.Field(attribute='long.side', column_name='long_side')
    long_open_price = fields.Field(attribute='long.open_price', column_name='long_open_price')
    long_close_price = fields.Field(attribute='long.close_price', column_name='long_close_price')
    long_volume = fields.Field(attribute='long.volume', column_name='long_volume')
    long_leverage = fields.Field(attribute='long.leverage', column_name='long_leverage')
    long_fees = fields.Field(attribute='long.fees', column_name='long_fees')
    long_funding = fields.Field(attribute='long.funding', column_name='long_funding')
    long_is_liquidated = fields.Field(attribute='long.is_liquidated', column_name='long_is_liquidated')
    long_open_at = fields.Field(attribute='long.open_at', column_name='long_open_at')
    long_close_at = fields.Field(attribute='long.close_at', column_name='long_close_at')

    short = fields.Field(
        attribute='short',
        column_name='short',
        widget=ForeignKeyWidget(CryptoDealItem, 'id')
    )
    long = fields.Field(
        attribute='long',
        column_name='long',
        widget=ForeignKeyWidget(CryptoDealItem, 'id')
    )

    class Meta:
        model = CryptoDeal
        # These are the fields that come directly from CryptoDeal
        # (IDs, creation timestamps, numeric fields, etc.). Adjust as needed.
        fields = (
            # Main CryptoDeal fields first:
            'id',
            'long',
            'short',
            'note',
            'pnl',
            'income',
            'fees',
            'funding',
            'roi',
            'roi_percent',
            'spread_open',
            'spread_close',
            'spread',
            'margin_open',
            'margin_close',
            'trading_volume',
            'created_at',
            'updated_at',
            # Then short item:
            'short_exchange',
            'short_symbol',
            'short_side',
            'short_open_price',
            'short_close_price',
            'short_volume',
            'short_leverage',
            'short_fees',
            'short_funding',
            'short_is_liquidated',
            'short_open_at',
            'short_close_at',
            # Then long item:
            'long_exchange',
            'long_symbol',
            'long_side',
            'long_open_price',
            'long_close_price',
            'long_volume',
            'long_leverage',
            'long_fees',
            'long_funding',
            'long_is_liquidated',
            'long_open_at',
            'long_close_at',
        )
        export_order = (
            # Main CryptoDeal fields first:
            'id',
            'note',
            'pnl',
            'income',
            'fees',
            'funding',
            'roi',
            'roi_percent',
            'spread_open',
            'spread_close',
            'spread',
            'margin_open',
            'margin_close',
            'trading_volume',
            'created_at',
            'updated_at',
            # Then short item:
            'short_exchange',
            'short_symbol',
            'short_side',
            'short_open_price',
            'short_close_price',
            'short_volume',
            'short_leverage',
            'short_fees',
            'short_funding',
            'short_is_liquidated',
            'short_open_at',
            'short_close_at',
            # Then long item:
            'long_exchange',
            'long_symbol',
            'long_side',
            'long_open_price',
            'long_close_price',
            'long_volume',
            'long_leverage',
            'long_fees',
            'long_funding',
            'long_is_liquidated',
            'long_open_at',
            'long_close_at',
        )

    def dehydrate_short_exchange(self, obj):
        """For exporting short exchange name."""
        if obj.short and obj.short.exchange:
            return obj.short.exchange.name
        return ''

    def dehydrate_short_symbol(self, obj):
        """For exporting short trading pair symbol."""
        if obj.short and obj.short.trading_pair:
            return obj.short.trading_pair.symbol
        return ''

    def dehydrate_short_side(self, obj):
        """For exporting short side."""
        return obj.short.side

    def dehydrate_short_open_price(self, obj):
        """For exporting short open price."""
        return obj.short.open_price

    def dehydrate_short_close_price(self, obj):
        """For exporting short close price."""
        return obj.short.close_price

    def dehydrate_short_volume(self, obj):
        """For exporting short volume."""
        return obj.short.volume

    def dehydrate_short_leverage(self, obj):
        """For exporting short leverage."""
        return obj.short.leverage

    def dehydrate_short_fees(self, obj):
        """For exporting short fees."""
        return obj.short.fees

    def dehydrate_short_funding(self, obj):
        """For exporting short funding."""
        return obj.short.funding

    def dehydrate_short_is_liquidated(self, obj):
        """For exporting short is liquidated."""
        return obj.short.is_liquidated

    def dehydrate_short_open_at(self, obj):
        """For exporting short open at."""
        return obj.short.open_at

    def dehydrate_short_close_at(self, obj):
        """For exporting short close at."""
        return obj.short.close_at

    def dehydrate_long_exchange(self, obj):
        """For exporting long exchange name."""
        if obj.long and obj.long.exchange:
            return obj.long.exchange.name
        return ''

    def dehydrate_long_symbol(self, obj):
        """For exporting long trading pair symbol."""
        if obj.long and obj.long.trading_pair:
            return obj.long.trading_pair.symbol
        return ''

    def dehydrate_long_side(self, obj):
        """For exporting long side."""
        return obj.long.side

    def dehydrate_long_open_price(self, obj):
        """For exporting long open price."""
        return obj.long.open_price

    def dehydrate_long_close_price(self, obj):
        """For exporting long close price."""
        return obj.long.close_price

    def dehydrate_long_volume(self, obj):
        """For exporting long volume."""
        return obj.long.volume

    def dehydrate_long_leverage(self, obj):
        """For exporting long leverage."""
        return obj.long.leverage

    def dehydrate_long_fees(self, obj):
        """For exporting long fees."""
        return obj.long.fees

    def dehydrate_long_funding(self, obj):
        """For exporting long funding."""
        return obj.long.funding

    def dehydrate_long_is_liquidated(self, obj):
        """For exporting long is liquidated."""
        return obj.long.is_liquidated

    def dehydrate_long_open_at(self, obj):
        """For exporting long open at."""
        return obj.long.open_at

    def dehydrate_long_close_at(self, obj):
        """For exporting long close at."""
        return obj.long.close_at

    # You can define similar `dehydrate_` methods for each short_ and long_ field
    # if you need fine-grained export formatting. Otherwise, the direct
    # `attribute='short.xxx'` or `attribute='long.xxx'` will suffice.

    @transaction.atomic
    def import_row(self, row, instance_loader, **kwargs):
        row_number = kwargs.get('row_number')
        # If needed, you can fetch the row number from kwargs:
        """
        Override import_row to handle the creation/updating
        of Exchange, TradingPair, and CryptoDealItem for both
        short and long sides before saving the main CryptoDeal.
        """
        # Extract short side info from row
        short_exchange_name = row.get('short_exchange')
        short_symbol = row.get('short_symbol')
        short_side = row.get('short_side')
        short_open_price = row.get('short_open_price')
        short_close_price = row.get('short_close_price')
        short_volume = row.get('short_volume')
        short_leverage = row.get('short_leverage')
        short_fees = row.get('short_fees')
        short_funding = row.get('short_funding')
        short_is_liquidated = row.get('short_is_liquidated')
        short_open_at = parse_datetime(row.get('short_open_at')) if row.get('short_open_at') else None
        short_close_at = parse_datetime(row.get('short_close_at')) if row.get('short_close_at') else None

        # Extract long side info from row
        long_exchange_name = row.get('long_exchange')
        long_symbol = row.get('long_symbol')
        long_side = row.get('long_side')
        long_open_price = row.get('long_open_price')
        long_close_price = row.get('long_close_price')
        long_volume = row.get('long_volume')
        long_leverage = row.get('long_leverage')
        long_fees = row.get('long_fees')
        long_funding = row.get('long_funding')
        long_is_liquidated = row.get('long_is_liquidated')
        long_open_at = parse_datetime(row.get('long_open_at')) if row.get('long_open_at') else None
        long_close_at = parse_datetime(row.get('long_close_at')) if row.get('long_close_at') else None

        # Create or get the short exchange
        short_exchange_obj = None
        if short_exchange_name:
            short_exchange_obj, _ = Exchange.objects.get_or_create(name=short_exchange_name)

        # Create or get the long exchange
        long_exchange_obj = None
        if long_exchange_name:
            long_exchange_obj, _ = Exchange.objects.get_or_create(name=long_exchange_name)

        # Create or get the short trading pair
        short_trading_pair_obj = None
        if short_symbol:
            # For example, if the symbol is 'BTC/USDT', split by '/'
            parts = short_symbol.split('/')
            if len(parts) == 2:
                base_currency, quote_currency = parts
            else:
                # Fallback if symbol doesn't contain '/'
                base_currency = short_symbol
                quote_currency = ''
            short_trading_pair_obj, _ = TradingPair.objects.get_or_create(
                base_currency=base_currency,
                quote_currency=quote_currency,
            )
            # The save method will set symbol automatically.

        # Create or get the long trading pair
        long_trading_pair_obj = None
        if long_symbol:
            parts = long_symbol.split('/')
            if len(parts) == 2:
                base_currency, quote_currency = parts
            else:
                base_currency = long_symbol
                quote_currency = ''
            long_trading_pair_obj, _ = TradingPair.objects.get_or_create(
                base_currency=base_currency,
                quote_currency=quote_currency,
            )

        # We will build or update short and long CryptoDealItem instances ourselves,
        # attach them to the row in memory, then proceed with the normal import flow.

        try:
            # We do not know if there's an existing PK in the row for the short or long,
            # so we always create new or update existing. Typically for a single CSV row
            # we are creating new items. If you want to handle updates, you'll need
            # logic to match on an identifier.

            short_item = CryptoDealItem()
            if short_exchange_obj:
                short_item.exchange = short_exchange_obj
            if short_trading_pair_obj:
                short_item.trading_pair = short_trading_pair_obj
            short_item.side = short_side or ''
            short_item.open_price = Decimal(short_open_price) if short_open_price else Decimal('0')
            short_item.close_price = Decimal(short_close_price) if short_close_price else Decimal('0')
            short_item.volume = Decimal(short_volume) if short_volume else Decimal('0')
            short_item.leverage = int(short_leverage) if short_leverage else 1
            short_item.fees = Decimal(short_fees) if short_fees else Decimal('0')
            short_item.funding = Decimal(short_funding) if short_funding else Decimal('0')
            short_item.is_liquidated = (str(short_is_liquidated).lower() == 'true')
            short_item.open_at = short_open_at or None
            short_item.close_at = short_close_at or None

            short_item.save()
            row['short'] = short_item.id
            row['short_id'] = short_item.id

            long_item = CryptoDealItem()
            if long_exchange_obj:
                long_item.exchange = long_exchange_obj
            if long_trading_pair_obj:
                long_item.trading_pair = long_trading_pair_obj
            long_item.side = long_side or ''
            long_item.open_price = Decimal(long_open_price) if long_open_price else Decimal('0')
            long_item.close_price = Decimal(long_close_price) if long_close_price else Decimal('0')
            long_item.volume = Decimal(long_volume) if long_volume else Decimal('0')
            long_item.leverage = int(long_leverage) if long_leverage else 1
            long_item.fees = Decimal(long_fees) if long_fees else Decimal('0')
            long_item.funding = Decimal(long_funding) if long_funding else Decimal('0')
            long_item.is_liquidated = (str(long_is_liquidated).lower() == 'true')
            long_item.open_at = long_open_at or None
            long_item.close_at = long_close_at or None

            long_item.save()
            row['long'] = long_item.id
            row['long_id'] = long_item.id

        except Exception as exc:
            raise exc
            result = super().import_row(row, instance_loader, **kwargs)
            # Record the error. The transaction will roll back anyway.
            row_errors = result.errors or []
            row_errors.append(Error(str(exc), row_number))
            result.errors = row_errors
            return result

        # Now that we have the short_item and long_item saved, we want to ensure
        # that the main CryptoDeal row references these two items. We'll inject
        # them into the incoming dataset so that the normal import logic
        # (which tries to create CryptoDeal) uses them.

        return super().import_row(row, instance_loader, **kwargs)


class CryptoDealItemResource(resources.ModelResource):
    class Meta:
        model = CryptoDealItem
        fields = (
            'id',
            'trading_pair',
            'exchange',
            'side',
            'open_price',
            'close_price',
            'volume',
            'leverage',
            'fees',
            'funding',
            'is_liquidated',
            'open_at',
            'close_at',
            'created_at',
            'updated_at',
            'trades',
            'pnl',
            'margin_open',
            'margin_close',
            'income',
            'roi',
            'roi_percent',
            'duration',
            'human_duration',
        )
