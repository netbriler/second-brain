import hashlib
import hmac
from decimal import Decimal
from time import time
from urllib.parse import urlencode

from aiogram.client.session import aiohttp

from arbitrage.exchanges.base import (
    AbstractExchange,
    BalanceSchema
)
from utils.logging import logger


class BinanceExchange(AbstractExchange):
    BASE_URL = 'https://api.binance.com'
    FUTURES_URL = 'https://fapi.binance.com'

    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key

    async def _send_signed_request(self, method: str, endpoint: str, params: dict = None, url_base='BASE'):
        """
        Helper method to send signed requests to Binance API.
        """
        base_urls = {
            'BASE': self.BASE_URL,
            'FUTURES': self.FUTURES_URL,
        }
        url = base_urls[url_base] + endpoint
        params = params or {}
        params['timestamp'] = int(time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        params['signature'] = signature
        headers = {'X-MBX-APIKEY': self.api_key}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, params=params) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f'Error sending request to Binance: {await response.text()}')
            logger.exception(e)

    async def _fetch_spot_balances(self) -> list[BalanceSchema]:
        """Fetch Spot balances."""
        balances = []
        try:
            spot_data = await self._send_signed_request('GET', '/api/v3/account', url_base='BASE')
            if not spot_data:
                return balances
            for asset in spot_data.get('balances', []):
                free = Decimal(asset['free'])
                locked = Decimal(asset['locked'])
                if not free and not locked:
                    continue
                balances.append(
                    BalanceSchema(
                        asset=asset['asset'],
                        account='spot',
                        free=free,
                        locked=locked,
                        raw=asset
                    )
                )
        except Exception as e:
            logger.exception(f'Error fetching spot balances: {e}')
        return balances

    async def _fetch_margin_balances(self) -> list[BalanceSchema]:
        """Fetch Margin balances."""
        balances = []
        try:
            margin_data = await self._send_signed_request('GET', '/sapi/v1/margin/account')
            if not margin_data:
                return balances
            for asset in margin_data.get('userAssets', []):
                free = Decimal(asset['free'])
                locked = Decimal(asset['locked'])
                borrowed = Decimal(asset['borrowed'])
                interest = Decimal(asset['interest'])
                net_asset = Decimal(asset['netAsset'])
                if not (free or locked or borrowed or interest or net_asset):
                    continue
                balances.append(
                    BalanceSchema(
                        asset=asset['asset'],
                        account='margin',
                        free=free,
                        locked=locked + borrowed + interest,
                        raw=asset,
                    )
                )
        except Exception as e:
            logger.exception(f'Error fetching margin balances: {e}')
        return balances

    async def _fetch_futures_balances(self) -> list[BalanceSchema]:
        """Fetch Futures balances."""
        balances = []
        try:
            futures_data = await self._send_signed_request('GET', '/fapi/v2/balance', url_base='FUTURES')
            if not futures_data:
                return balances
            for asset in futures_data:
                free = Decimal(asset['availableBalance'])
                locked = Decimal(asset['balance']) - free
                if not free and not locked:
                    continue
                balances.append(
                    BalanceSchema(
                        asset=asset['asset'],
                        account='futures',
                        free=free,
                        locked=locked,
                        raw=asset
                    )
                )
        except Exception as e:
            logger.exception(f'Error fetching futures balances: {e}')
        return balances

    async def _fetch_funding_balances(self) -> list[BalanceSchema]:
        """Fetch Funding balances."""
        balances = []
        try:
            funding_data = await self._send_signed_request('POST', '/sapi/v1/asset/get-funding-asset')
            if not funding_data:
                return balances
            for asset in funding_data:
                free = Decimal(asset['free'])
                locked = Decimal(asset['locked'])
                if not free and not locked:
                    continue
                balances.append(
                    BalanceSchema(
                        asset=asset['asset'],
                        account='funding',
                        free=free,
                        locked=locked,
                        raw=asset,
                    )
                )
        except Exception as e:
            logger.exception(f'Error fetching funding balances: {e}')
        return balances

    async def _fetch_earn_balances(self) -> list[BalanceSchema]:
        balances_by_asset = {}

        try:
            flexible_data = await self._send_signed_request(
                'GET',
                '/sapi/v1/simple-earn/flexible/position',
            )

            for entry in flexible_data.get('rows', []):
                free = Decimal(entry['totalAmount'])
                if not free:
                    continue
                balance = BalanceSchema(
                    asset=entry['asset'],
                    account='earn',
                    free=free,
                    locked=Decimal('0'),
                    raw=[entry],
                )
                balances_by_asset[entry['asset']] = balance
        except Exception as e:
            logger.exception(f'Error fetching flexible savings balances: {e}')

        try:
            locked_data = await self._send_signed_request(
                'GET',
                '/sapi/v1/simple-earn/locked/position',
            )

            for entry in locked_data.get('rows', []):
                locked = Decimal(entry['amount'])
                if not locked:
                    continue

                balance = balances_by_asset.get(
                    entry['asset'],
                )
                if not balance:
                    balance = BalanceSchema(
                        asset=entry['asset'],
                        account='earn',
                        free=Decimal('0'),
                        locked=locked,
                        raw=[entry],
                    )
                    balances_by_asset[entry['asset']] = balance
                else:
                    balance.locked += locked
                    if not balance.raw:
                        balance.raw = []
                    balance.raw.append(entry)
        except Exception as e:
            logger.exception(f'Error fetching locked savings balances: {e}')

        return list(balances_by_asset.values())

    async def fetch_balances(self) -> list[BalanceSchema]:
        """
        Aggregate Spot, Margin, Futures, Funding, and Earn balances.
        """
        all_balances = []

        spot_balances = await self._fetch_spot_balances()
        margin_balances = await self._fetch_margin_balances()
        futures_balances = await self._fetch_futures_balances()
        funding_balances = await self._fetch_funding_balances()
        earn_balances = await self._fetch_earn_balances()

        all_balances.extend(spot_balances)
        all_balances.extend(margin_balances)
        all_balances.extend(futures_balances)
        all_balances.extend(funding_balances)
        all_balances.extend(earn_balances)

        return all_balances
