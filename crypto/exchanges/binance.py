import asyncio
import hashlib
import hmac
from datetime import datetime, timedelta
from decimal import Decimal
from time import time
from urllib.parse import urlencode

from aiogram.client.session import aiohttp

from crypto.exchanges.base import AbstractExchange, BalanceSchema
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
            hashlib.sha256,
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
                        raw=asset,
                    ),
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
                    ),
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
                        raw=asset,
                    ),
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
                    ),
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

    async def get_all_movements(self, start_time: int = None, end_time: int = None):
        """
        Fetches all asset movements: deposits, withdrawals, transfers, earn rewards, and dividends.
        Returns a list of unified movement records.
        """

        if not start_time:
            # Default to last 90 days (max allowed for some endpoints)
            start_time = int((datetime.utcnow() - timedelta(days=90)).timestamp() * 1000)
        if not end_time:
            end_time = int(datetime.utcnow().timestamp() * 1000)

        tasks = [
            self._send_signed_request(
                'GET', '/sapi/v1/capital/deposit/hisrec', {
                    'startTime': start_time,
                    'endTime': end_time,
                },
            ),
            self._send_signed_request(
                'GET', '/sapi/v1/capital/withdraw/history', {
                    'startTime': start_time,
                    'endTime': end_time,
                },
            ),
            self._send_signed_request(
                'GET', '/sapi/v1/asset/transfer', {
                    'type': 0,  # all types
                    'startTime': start_time,
                    'endTime': end_time,
                },
            ),
            self._send_signed_request(
                'GET', '/sapi/v1/asset/assetDividend', {
                    'startTime': start_time,
                    'endTime': end_time,
                },
            ),
            self._send_signed_request(
                'GET', '/sapi/v1/simple-earn/flexible/history/rewardsRecord', {
                    'startTime': start_time,
                    'endTime': end_time,
                    'type': 'ALL',
                },
            ),
        ]

        try:
            deposit_data, withdraw_data, transfer_data, dividend_data, earn_data = await asyncio.gather(*tasks)

            movements = []

            for d in deposit_data:
                movements.append(
                    {
                        'type': 'deposit',
                        'asset': d['coin'],
                        'amount': d['amount'],
                        'status': d['status'],
                        'time': d['insertTime'],
                    },
                )

            for w in withdraw_data:
                movements.append(
                    {
                        'type': 'withdrawal',
                        'asset': w['coin'],
                        'amount': w['amount'],
                        'status': w['status'],
                        'time': w['applyTime'],
                    },
                )

            for t in transfer_data.get('rows', []):
                movements.append(
                    {
                        'type': 'internal_transfer',
                        'asset': t['asset'],
                        'amount': t['qty'],
                        'from': t['fromAccountType'],
                        'to': t['toAccountType'],
                        'time': t['timestamp'],
                    },
                )

            for r in dividend_data.get('rows', []):
                movements.append(
                    {
                        'type': 'dividend',
                        'asset': r['asset'],
                        'amount': r['amount'],
                        'info': r['tranId'],
                        'time': r['divTime'],
                    },
                )

            for e in earn_data:
                movements.append(
                    {
                        'type': 'earn_reward',
                        'asset': e['asset'],
                        'amount': e['interest'],
                        'time': e['time'],
                    },
                )

            return sorted(movements, key=lambda x: x['time'])
        except Exception as e:
            logger.exception('Failed to fetch all movements')
            return []
