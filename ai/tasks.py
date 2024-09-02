from pathlib import Path

from django.utils.translation import activate
from django.utils.translation import gettext as _
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReactionTypeEmoji

from ai.constants import AITasksCategories
from ai.services.base import save_ai_response
from ai.services.text_recognation import (
    determine_category_and_format_text,
    google_translate_speech_to_text,
    transcribe_using_genai,
    transcribe_using_openai,
)
from app import settings
from app.celery import LoggingTask, app
from telegram_bot.loader import get_sync_bot
from telegram_bot.models import File
from telegram_bot.services.files import sync_send_file_to_user
from users.models import User
from utils.logging import logger


@app.task(
    base=LoggingTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
)
def transcribe_genai_task(chat_id: int, file_id: int, destination: str, message_id: int = None, debug: bool = False):
    bot = get_sync_bot()

    file = File.objects.get(id=file_id)

    transcription_genai = transcribe_using_genai(Path(destination), mime_type=file.mime_type)
    if transcription_genai.error_message:
        bot.send_message(
            chat_id,
            f'Genai error:\n\n{transcription_genai.error_message}\n\nTook{transcription_genai.time_spent:.6f}s',
            reply_to_message_id=message_id,
        )
        raise Exception('Error transcribing using Genai')

    if debug:
        bot.send_message(
            chat_id,
            f'GenaI:\n\n{transcription_genai.text_recognition}\n\nTook {transcription_genai.time_spent:.6f}s',
            reply_to_message_id=message_id,
        )

    file.refresh_from_db()
    file.raw_data['transcription_genai'] = transcription_genai.text_recognition
    file.save(
        update_fields=[
            'raw_data',
        ],
    )

    determine_category_task.delay(chat_id, file.uploaded_by.id, transcription_genai.text_recognition, message_id)

    save_ai_response(transcription_genai, source=file, requested_by=file.uploaded_by)

    return True


@app.task(
    base=LoggingTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
)
def transcribe_openai_task(chat_id: int, file_id: int, destination: str, message_id: int = None, debug: bool = False):
    bot = get_sync_bot()

    file = File.objects.get(id=file_id)

    transcription_openai = transcribe_using_openai(Path(destination))
    if transcription_openai.error_message:
        bot.send_message(
            chat_id,
            f'Openai error:\n\n{transcription_openai.error_message}\n\nTook {transcription_openai.time_spent:.6f}s',
            reply_to_message_id=message_id,
        )
        raise Exception('Error transcribing using OpenAI')

    if debug:
        bot.send_message(
            chat_id,
            f'Openai:\n\n{transcription_openai.text_recognition}\n\nTook {transcription_openai.time_spent:.6f}s',
            reply_to_message_id=message_id,
        )

    file.refresh_from_db()
    file.raw_data['transcription_openai'] = transcription_openai.text_recognition
    file.save(
        update_fields=[
            'raw_data',
        ],
    )

    determine_category_task.delay(chat_id, file.uploaded_by.id, transcription_openai.text_recognition, message_id)

    save_ai_response(transcription_openai, source=file, requested_by=file.uploaded_by)

    return True


@app.task(
    base=LoggingTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
)
def transcribe_google_translate_task(
    chat_id: int,
    file_id: int,
    destination: str,
    message_id: int = None,
    debug: bool = False,
):
    bot = get_sync_bot()

    file = File.objects.get(id=file_id)

    transcription_google_translate = google_translate_speech_to_text(Path(destination), 'ru-RU')
    if not transcription_google_translate:
        bot.send_message(
            chat_id,
            f'Google translate error:\n\n{transcription_google_translate.error_message}\n\n'
            f'Took {transcription_google_translate.time_spent:.6f}s',
            reply_to_message_id=message_id,
        )
        raise Exception('Error transcribing using Google Translate')

    if debug:
        bot.send_message(
            chat_id,
            f'google_translate:\n\n{transcription_google_translate.text_recognition}'
            f'\n\nTook {transcription_google_translate.time_spent:.6f}s',
            reply_to_message_id=message_id,
        )

    file.refresh_from_db()
    file.raw_data['transcription_google_translate'] = transcription_google_translate.text_recognition
    file.save(
        update_fields=[
            'raw_data',
        ],
    )

    determine_category_task.delay(
        chat_id,
        file.uploaded_by.id,
        transcription_google_translate.text_recognition,
        message_id,
    )

    save_ai_response(transcription_google_translate, source=file, requested_by=file.uploaded_by)

    return True


@app.task(
    base=LoggingTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
)
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
    file_extension = file_path.split('.')[-1]

    logger.debug(f'Downloading file {file_path}')

    bot.send_chat_action(chat_id, 'record_voice')
    destination = settings.BASE_DIR / f'temp/{file.file_unique_id}.{file_extension}'
    if not Path.exists(destination.parent):
        Path.mkdir(destination.parent, parents=True)

    # if file is not downloaded, download it
    if not Path.exists(destination):
        downloaded_file = bot.download_file(file_path)
        with Path.open(destination, 'wb') as new_file:
            new_file.write(downloaded_file)

    # transcribe_genai_task.delay(chat_id, db_file.id, str(destination), message_id)
    transcribe_openai_task.delay(chat_id, db_file.id, str(destination), message_id)
    # transcribe_google_translate_task.delay(chat_id, db_file.id, str(destination), message_id)

    return True


@app.task(
    base=LoggingTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
)
def send_file_to_user_task(file_id: int, user_id: int):
    bot = get_sync_bot()
    user = User.objects.get(id=user_id)
    logger.debug(f'Sending file {file_id} to user {user}')
    activate(user.language_code)

    file = File.objects.get(id=file_id)

    sync_send_file_to_user(bot, file, user)

    return True


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
    if result.error_message:
        bot.send_message(
            chat_id,
            f'Error determining category {result.error_message}',
            reply_to_message_id=message_id,
        )
        raise Exception('Error determining category')

    markup = InlineKeyboardMarkup()
    for category in result.text_recognition.category_predictions:
        text = str(AITasksCategories[category].label)
        markup.add(InlineKeyboardButton(text, callback_data=f'category_{category}'))

    bot.send_message(
        chat_id,
        _('Message: {text}\n\nChoose the category:').format(text=result.text_recognition.text),
        reply_to_message_id=message_id,
        reply_markup=markup,
    )

    save_ai_response(result, requested_by=user)

    return True
