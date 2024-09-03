from django.db.models.signals import post_save
from django.dispatch import receiver

from telegram_bot.constants import MessageRoles
from telegram_bot.models import Message
from telegram_bot.signals import (
    message_for_recognition_created,
    message_for_transcription_created,
)


# on message create
@receiver(
    post_save,
    sender=Message,
)
def message_created(
    sender,
    instance: Message,
    created,
    **kwargs,
):
    if created:
        if instance.role == MessageRoles.TEXT_RECOGNITION.value[0]:
            message_for_recognition_created.send(Message, instance=instance)
        elif instance.role == MessageRoles.VOICE_RECOGNITION.value[0]:
            message_for_transcription_created.send(Message, instance=instance)
