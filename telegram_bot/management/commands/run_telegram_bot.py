import asyncio

from django.core.management.base import BaseCommand

from telegram_bot.handlers import dp
from telegram_bot.loader import bot
from utils.logging import logger


class Command(BaseCommand):
    help = 'Start telegram_bot'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        logger.info('Starting telegram_bot')

        async def main() -> None:
            await dp.start_polling(bot)

        asyncio.run(main())

        logger.info('Finished telegram_bot')
