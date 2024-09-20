import logging

from django.core.management.base import BaseCommand

from workflows.manager import manager


class Command(BaseCommand):
    help = 'Run a worker'

    def handle(self, *args, **options):
        logging.info('Starting worker')
        manager.run(None)
