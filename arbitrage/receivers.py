from django.db.models.signals import post_save
from django.dispatch import receiver

from arbitrage.models import ArbitrageDealItem, ArbitrageDeal


# on message create
@receiver(
    post_save,
    sender=ArbitrageDealItem,
)
def message_created(
        sender,
        instance: ArbitrageDealItem,
        created,
        **kwargs,
):
    for s in ArbitrageDeal.objects.filter(
        short=instance,
    ):
        s.save()

    for l in ArbitrageDeal.objects.filter(
        long=instance,
    ):
        l.save()
