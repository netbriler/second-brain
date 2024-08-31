from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, PeriodicTask


class Command(BaseCommand):
    help = 'Create periodic tasks that required for work'

    def handle(self, *args, **options):
        every_1_seconds, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.SECONDS,
        )

        every_3_seconds, _ = IntervalSchedule.objects.get_or_create(
            every=3,
            period=IntervalSchedule.SECONDS,
        )

        every_5_seconds, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.SECONDS,
        )

        every_15_seconds, _ = IntervalSchedule.objects.get_or_create(
            every=15,
            period=IntervalSchedule.SECONDS,
        )

        every_1_minute, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )

        every_10_minutes, _ = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.MINUTES,
        )

        every_15_minutes, _ = IntervalSchedule.objects.get_or_create(
            every=15,
            period=IntervalSchedule.MINUTES,
        )

        every_1_hour, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )

        every_24_hour, _ = IntervalSchedule.objects.get_or_create(
            every=24,
            period=IntervalSchedule.HOURS,
        )

        PeriodicTask.objects.get_or_create(
            task='courses.tasks.reminders',
            defaults={
                'name': 'reminders',
                'interval': every_1_hour,
            },
        )
