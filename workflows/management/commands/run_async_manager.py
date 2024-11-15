import asyncio
import logging

from django.core.management.base import BaseCommand

from telegram_restricted_downloader.workflows.restricted_downloader import RestrictedDownloaderWorkflow
from workflows.manager import async_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


class Command(BaseCommand):
    help = 'Run a worker asynchronously'

    async def handle_async(self, *args, **options):
        logging.info('Starting async worker')

        await async_manager.create_process(
            None, RestrictedDownloaderWorkflow, stage_data={
                'from_account_id': 10,
                'channel_id': -1002025969435
            }
        )

        await async_manager.run(None)

    def handle(self, *args, **options):
        asyncio.run(self.handle_async(*args, **options))
