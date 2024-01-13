import asyncio

from django.core.management.base import BaseCommand

from telegram_bot.start_bot import start_polling
from utils.logging import logger


class Command(BaseCommand):
    help = 'Start telegram_bot'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        logger.info('Starting telegram_bot')

        asyncio.run(start_polling())

        logger.info('Finished telegram_bot')
