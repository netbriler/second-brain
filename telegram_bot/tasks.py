from pathlib import Path
from time import time

from django.utils.translation import activate
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReactionTypeEmoji

from app import settings
from app.celery import LoggingTask, app
from telegram_bot.models import File
from telegram_bot.services.files import sync_send_file_to_user
from users.models import User
from utils.logging import logger

from .loader import get_sync_bot
from .services.text_recognation import (
    determine_category_and_format_text,
    free_speech_to_text,
    transcribe_using_genai,
    transcribe_using_openai,
)


@app.task(base=LoggingTask)
def transcribe_genai_task(chat_id: int, file_id: int, destination: str, message_id: int = None):
    bot = get_sync_bot()

    file = File.objects.get(id=file_id)

    time_start = time()
    transcription_genai = transcribe_using_genai(Path(destination), mime_type=file.raw_data.get('mime_type', None))
    bot.send_message(
        chat_id,
        f'GenaI:\n\n{transcription_genai}\n\nTook {time() - time_start:.6f}s',
        reply_to_message_id=message_id,
    )

    file.refresh_from_db()
    file.raw_data['transcription_genai'] = transcription_genai
    file.save(
        update_fields=[
            'raw_data',
        ],
    )


@app.task(base=LoggingTask)
def transcribe_openai_task(chat_id: int, file_id: int, destination: str, message_id: int = None):
    bot = get_sync_bot()

    file = File.objects.get(id=file_id)

    time_start = time()
    transcription_openai = transcribe_using_openai(Path(destination))
    bot.send_message(
        chat_id,
        f'Openai:\n\n{transcription_openai}\n\nTook {time() - time_start:.6f}s',
        reply_to_message_id=message_id,
    )

    file.refresh_from_db()
    file.raw_data['transcription_openai'] = transcription_openai
    file.save(
        update_fields=[
            'raw_data',
        ],
    )


@app.task(base=LoggingTask)
def transcribe_free_task(chat_id: int, file_id: int, destination: str, message_id: int = None):
    bot = get_sync_bot()

    file = File.objects.get(id=file_id)

    time_start = time()
    transcription_free = free_speech_to_text(destination, 'ru-RU')
    bot.send_message(
        chat_id,
        f'Free:\n\n{transcription_free}\n\nTook {time() - time_start:.6f}s',
        reply_to_message_id=message_id,
    )

    file.refresh_from_db()
    file.raw_data['transcription_free'] = transcription_free
    file.save(
        update_fields=[
            'raw_data',
        ],
    )


@app.task(base=LoggingTask)
def transcribe_file_task(chat_id: int, file_id: int, user_id: int, message_id: int = None):
    bot = get_sync_bot()
    logger.debug(f'Transcribing file {file_id} for user {user_id}')

    user = User.objects.get(id=user_id)
    logger.debug(f'Transcribing file {file_id} for user {user}')
    activate(user.language_code)

    db_file = File.objects.get(id=file_id)
    if not message_id:
        message_id, message_id2 = sync_send_file_to_user(bot, db_file, user)

    bot.set_message_reaction(chat_id, message_id, [ReactionTypeEmoji('👀')])

    # Download the file
    file = bot.get_file(db_file.file_id)
    file_path = file.file_path

    logger.debug(f'Downloading file {file_path}')
    bot.send_chat_action(chat_id, 'record_voice')
    destination = settings.BASE_DIR / f'temp/{file.file_id}.ogg'
    downloaded_file = bot.download_file(file_path)
    with Path.open(destination, 'wb') as new_file:
        new_file.write(downloaded_file)

    transcribe_genai_task.delay(chat_id, db_file.id, str(destination), message_id)
    transcribe_openai_task.delay(chat_id, db_file.id, str(destination), message_id)
    transcribe_free_task.delay(chat_id, db_file.id, str(destination), message_id)


@app.task(base=LoggingTask)
def send_file_to_user_task(file_id: int, user_id: int):
    bot = get_sync_bot()
    user = User.objects.get(id=user_id)
    logger.debug(f'Sending file {file_id} to user {user}')
    activate(user.language_code)

    file = File.objects.get(id=file_id)

    sync_send_file_to_user(bot, file, user)


@app.task(
    base=LoggingTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
)
def determine_category_task(chat_id: int, user_id: int, message: str, message_id: int = None):
    bot = get_sync_bot()

    user = User.objects.get(id=user_id)
    logger.debug(f'Determining category for message {message} for user {user}')
    activate(user.language_code)

    result = determine_category_and_format_text(message)

    if not result:
        bot.send_message(
            chat_id,
            'Error determining category',
            reply_to_message_id=message_id,
        )
        raise Exception('Error determining category')

    markup = InlineKeyboardMarkup()
    for category in result.category_predictions:
        markup.add(InlineKeyboardButton(category, callback_data=f'category_{category}'))

    bot.send_message(
        chat_id,
        f'Message: {result.text}\n\nChoose the category:',
        reply_to_message_id=message_id,
        reply_markup=markup,
    )
