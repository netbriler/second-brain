import asyncio

from django.core.management.base import BaseCommand

from crypto.exchanges.binance import BinanceExchange


class Command(BaseCommand):
    help = 'Start telegram bot polling'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        async def main():
            binance = BinanceExchange(
                api_key='F8nG6szxGg8P9C9uJalUXHdcING6MnlQhSHxn7kYWAcYT2d7ijMqYN9wsCPpiaNv',
                secret_key='58z8kF4ipFIEf8Q6Cf1VHztFWC8EQQ6lRDCP2tPHNO3dWowKMdSKuCA6j0bUZFfE',
            )

            print(
                await binance.get_all_movements(),
            )
            # balances = await binance.fetch_balances()

            # for binance_balance in balances:
            #     if binance_balance.asset != 'USDT':
            #         continue
            #     print(binance_balance)

        asyncio.run(main())
