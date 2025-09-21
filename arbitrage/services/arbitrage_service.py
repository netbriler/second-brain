from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.utils.timesince import timesince

Q2 = Decimal('0.01')
ZERO = Decimal('0.0')
HUNDRED = Decimal('100.0')
DAYS_IN_YEAR = Decimal('365.25')


class ArbitrageService:
    @staticmethod
    def _q2(x: Decimal | None) -> Decimal:
        return (x or ZERO).quantize(Q2, rounding=ROUND_HALF_UP)

    @staticmethod
    def _spread(short_open: Decimal, long_open: Decimal, short_close: Decimal, long_close: Decimal):
        spread_open = ((short_open / long_open) - 1) * HUNDRED if short_open and long_open else ZERO
        spread_close = ((short_close / long_close) - 1) * HUNDRED if short_close and long_close else ZERO
        return (
            ArbitrageService._q2(spread_open),
            ArbitrageService._q2(spread_close),
            ArbitrageService._q2(spread_open - spread_close),
        )

    @staticmethod
    def _apr_percent(income: Decimal, margin_open: Decimal, duration: timedelta) -> Decimal:
        if not (income and margin_open and duration and duration.total_seconds() > 0):
            return ZERO
        days = Decimal(str(duration.total_seconds() / 86400))
        return ArbitrageService._q2((income / margin_open) * (DAYS_IN_YEAR / days) * HUNDRED)

    @staticmethod
    def apply_item(item: 'ArbitrageDealItem', user: 'User' = None):
        if user:
            item.user = user
        item.margin_close = ZERO
        item.duration = None
        item.human_duration = None

        item.pnl = ZERO
        if item.close_price is not None:
            if item.side in ('short', 'margin-short'):
                item.pnl = (item.open_price - item.close_price) * item.volume
            else:
                item.pnl = (item.close_price - item.open_price) * item.volume

        item.income = item.pnl
        if item.fees:
            item.income += item.fees
        if item.funding:
            item.income += item.funding

        item.margin_open = (item.open_price * item.volume / item.leverage) + item.extra_margin
        if item.close_price is not None:
            item.margin_close = item.margin_open + item.income

        item.trading_volume = abs(
            item.volume * item.open_price * Decimal(item.leverage)
        )
        if item.close_price is not None:
            item.trading_volume += abs(item.volume * item.close_price * Decimal(item.leverage))

        item.roi = item.income / item.margin_open if item.margin_open else ZERO
        item.roi_percent = ArbitrageService._q2(item.roi * HUNDRED)

        if item.open_at and item.close_at:
            item.duration = item.close_at - item.open_at
            item.human_duration = timesince(item.open_at, item.close_at)
        return item

    @staticmethod
    def apply_arbitrage_deal(deal: 'ArbitrageDeal'):
        deal.duration = None
        deal.human_duration = None
        deal.spread_open = ZERO
        deal.spread_close = ZERO
        deal.spread = ZERO
        deal.trading_volume = ZERO
        deal.apr_percent = ZERO

        short = deal.short
        long = deal.long
        if not (short and long):
            return deal

        ArbitrageService.apply_item(short, deal.user)
        short.save()
        ArbitrageService.apply_item(long, deal.user)
        long.save()

        deal.exchanges = f'{short.exchange} - {long.exchange}' if short.exchange != long.exchange else f'{short.exchange}'

        deal.pnl = short.pnl + long.pnl
        deal.income = short.income + long.income
        deal.fees = short.fees + long.fees
        deal.funding = short.funding + long.funding

        deal.margin_open = short.margin_open + long.margin_open
        deal.margin_close = short.margin_close + long.margin_close

        deal.spread_open, deal.spread_close, deal.spread = ArbitrageService._spread(
            short.open_price, long.open_price,
            short.close_price, long.close_price
        )

        deal.trading_volume = abs(
            short.trading_volume + long.trading_volume
        )

        if short.open_at and long.open_at and short.close_at and long.close_at:
            deal.duration = max(short.close_at, long.close_at) - min(short.open_at, long.open_at)
            deal.human_duration = timesince(min(short.open_at, long.open_at), max(short.close_at, long.close_at))

        deal.roi = deal.income / deal.margin_open if deal.margin_open else ZERO
        deal.roi_percent = ArbitrageService._q2(deal.roi * HUNDRED)
        deal.apr_percent = ArbitrageService._apr_percent(deal.income, deal.margin_open, deal.duration)

        return deal

    @staticmethod
    def apply_trade_deal(deal: 'ArbitrageDeal'):
        deal.duration = None
        deal.human_duration = None
        deal.spread_open = ZERO
        deal.spread_close = ZERO
        deal.spread = ZERO
        deal.trading_volume = ZERO
        deal.apr_percent = ZERO

        pos = deal.short or deal.long
        if not pos:
            return deal

        ArbitrageService.apply_item(pos)
        pos.save()

        deal.exchanges = pos.exchange.name
        deal.pnl = pos.pnl
        deal.income = pos.income
        deal.fees = pos.fees
        deal.funding = pos.funding
        deal.margin_open = pos.margin_open
        deal.margin_close = pos.margin_close

        deal.trading_volume = abs(pos.trading_volume)

        if pos.open_at and pos.close_at:
            deal.duration = pos.close_at - pos.open_at
            deal.human_duration = timesince(pos.open_at, pos.close_at)

        deal.roi = deal.income / pos.margin_open if pos.margin_open else ZERO
        deal.roi_percent = ArbitrageService._q2(deal.roi * HUNDRED)
        deal.apr_percent = ArbitrageService._apr_percent(deal.income, deal.margin_open, deal.duration)

        return deal

    @staticmethod
    def apply_deal(deal: 'ArbitrageDeal'):
        if deal.type == deal.DealType.ARBITRAGE:
            return ArbitrageService.apply_arbitrage_deal(deal)
        return ArbitrageService.apply_trade_deal(deal)
