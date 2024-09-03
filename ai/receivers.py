from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver

from ai.tasks import determine_category_task, transcribe_file_task
from telegram_bot.models import Message
from telegram_bot.signals import (
    message_for_recognition_created,
    message_for_transcription_created,
)


@receiver(message_for_recognition_created)
def handle_message_for_recognition(sender, instance: Message, **kwargs):
    determine_category_task.delay(
        chat_id=instance.chat_id,
        user_id=instance.user.id,
        message=instance.text,
        message_id=instance.message_id,
        source_id=instance.id,
        source_type_id=ContentType.objects.get_for_model(Message).id,
    )


@receiver(message_for_transcription_created)
def handle_message_for_transcription(sender, instance: Message, **kwargs):
    transcribe_file_task.delay(
        chat_id=instance.chat_id,
        message_id=instance.message_id,
        file_id=instance.file.id,
        user_id=instance.user.id,
        source_id=instance.id,
        source_type_id=ContentType.objects.get_for_model(Message).id,
    )
