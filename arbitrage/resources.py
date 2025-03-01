from import_export import resources

from .models import ArbitrageDeal, ArbitrageDealItem


class ArbitrageDealResource(resources.ModelResource):
    class Meta:
        model = ArbitrageDeal
        fields = (
            'id',
            'short',
            'long',
            'note',
            'created_at',
            'updated_at',
            'exchanges',
        )
        export_order = fields


class ArbitrageDealItemResource(resources.ModelResource):
    class Meta:
        model = ArbitrageDealItem
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
        )
