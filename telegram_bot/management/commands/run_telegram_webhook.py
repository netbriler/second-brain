from django.core.management.base import BaseCommand

from telegram_bot.start_bot import start_webhook


class Command(BaseCommand):
    help = 'Start telegram bot webhook'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        start_webhook()
