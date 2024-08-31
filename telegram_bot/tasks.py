import random
from pathlib import Path

import google.generativeai as genai
from django.utils.translation import activate
from django.utils.translation import gettext as _
from telebot.types import ReactionTypeEmoji

from app import settings
from app.celery import LoggingTask, app
from telegram_bot.models import File
from telegram_bot.services.files import sync_send_file_to_user
from users.models import User
from utils.logging import logger

from .loader import get_sync_bot


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

    # Configure generative AI model
    genai.configure(api_key=random.choice(settings.GOOGLE_GEMINI_API_KEYS))
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Download the file
    file = bot.get_file(db_file.file_id)
    file_path = file.file_path

    logger.debug(f'Downloading file {file_path}')
    bot.send_chat_action(chat_id, 'record_voice')
    destination = settings.BASE_DIR / f'temp/{file.file_id}.ogg'
    downloaded_file = bot.download_file(file_path)
    with Path.open(destination, 'wb') as new_file:
        new_file.write(downloaded_file)

    # Upload file and generate content
    logger.debug(f'Sending file to genai {destination}')
    try:
        file = genai.upload_file(destination, mime_type=db_file.raw_data.get('mime_type', None))
    except Exception as e:  # noqa
        logger.exception(f'Error uploading file to genai: {e}')
        bot.send_message(
            chat_id,
            _('Something went wrong during file upload.'),
            reply_to_message_id=message_id,
        )
        return

    if not file:
        raise Exception('File not found after upload attempt.')

    logger.debug(f'Generating content for file {destination}')
    try:
        result = model.generate_content(
            [
                file,
                'Only transcribe audio to text',
            ],
        )
        bot.send_message(chat_id, result.text, reply_to_message_id=message_id)

        db_file.raw_data['transcription'] = result.text
        db_file.save(
            update_fields=[
                'raw_data',
            ],
        )

    except Exception as e:  # noqa
        logger.exception(f'Error generating content from genai: {e}')
        bot.send_message(
            chat_id,
            _('Something went wrong during content generation.'),
            reply_to_message_id=message_id,
        )


@app.task(base=LoggingTask)
def send_file_to_user_task(file_id: int, user_id: int):
    bot = get_sync_bot()
    user = User.objects.get(id=user_id)
    logger.debug(f'Sending file {file_id} to user {user}')
    activate(user.language_code)

    file = File.objects.get(id=file_id)

    sync_send_file_to_user(bot, file, user)
