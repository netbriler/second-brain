import asyncio

from django.core.management.base import BaseCommand

from telegram_bot.start_bot import start_polling


class Command(BaseCommand):
    help = 'Start telegram bot polling'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        asyncio.run(start_polling())
