import asyncio
import logging

from django.core.management.base import BaseCommand

from workflows.manager import async_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()],
)


class Command(BaseCommand):
    help = 'Run a worker asynchronously'

    async def handle_async(self, *args, **options):
        logging.info('Starting async worker')

        await async_manager.run(None)

    def handle(self, *args, **options):
        asyncio.run(self.handle_async(*args, **options))
