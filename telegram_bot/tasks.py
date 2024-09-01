import random
from pathlib import Path
from time import time

import google.generativeai as genai
import speech_recognition as sr
from django.utils.translation import activate
from openai import OpenAI
from pydub import AudioSegment
from telebot.types import ReactionTypeEmoji

from app import settings
from app.celery import LoggingTask, app
from telegram_bot.models import File
from telegram_bot.services.files import sync_send_file_to_user
from users.models import User
from utils.logging import logger

from .loader import get_sync_bot


def transcribe_using_openai(file_path: Path):
    logger.debug(f'Transcribing file {file_path} using OpenAI')
    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
    )

    audio_file = Path.open(file_path, 'rb')
    transcription = client.audio.transcriptions.create(
        model='whisper-1',
        file=audio_file,
    )
    return transcription.text


def transcribe_using_genai(file_path: Path, mime_type: str = None) -> str | None:
    # Configure generative AI model
    genai.configure(api_key=random.choice(settings.GOOGLE_GEMINI_API_KEYS))
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Upload file and generate content
    logger.debug(f'Sending file to genai {file_path}')
    try:
        file = genai.upload_file(file_path, mime_type=mime_type)
    except Exception as e:  # noqa
        logger.exception(f'Error uploading file to genai: {e}')
        return  # noqa

    if not file:
        return  # noqa

    logger.debug(f'Generating content for file {file_path}')
    try:
        result = model.generate_content(
            [
                file,
                'Transcribe the audio to text, correct grammar, and add punctuation.'
                ' Remove filler words and stutters such as "Э", "ммм", and similar sounds.',
            ],
        )
    except Exception as e:  # noqa
        logger.exception(f'Error generating content from genai: {e}')
    else:
        return result.text


def free_speech_to_text(path: Path, language: str) -> str:
    """
    Transcribes an audio file at the given path to text and writes the transcribed text to the output file.
    """
    file_path = Path(path)

    if file_path.suffix == '.wav':
        wav_file = str(file_path)
    elif file_path.suffix in ('.mp3', '.m4a', '.ogg', '.flac'):
        audio_file = AudioSegment.from_file(
            file_path,
            format=file_path.suffix[1:],
        )
        wav_file = str(file_path.with_suffix('.wav'))
        audio_file.export(wav_file, format='wav')
    else:
        raise ValueError(
            f'Unsupported audio format: {file_path.suffix}',
        )

    with sr.AudioFile(wav_file) as source:
        audio_data = sr.Recognizer().record(source)
        r = sr.Recognizer()
        text = r.recognize_google(audio_data, language=language)
        return text


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
