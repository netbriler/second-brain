import random
from pathlib import Path
from time import time

import google.generativeai as genai
import speech_recognition as sr
from google.ai.generativelanguage_v1beta import Schema, Type
from loguru import logger
from openai import OpenAI
from pydub import AudioSegment

from ai.constants import AIMessageCategories, AITasksCategories
from ai.services.base import (
    ReminderRecognition,
    ReminderRecognitionResponse,
    TextRecognition,
    TextRecognitionResponse,
    VoiceRecognitionResponse,
)
from app import settings

genai.configure(api_key=random.choice(settings.GOOGLE_GEMINI_API_KEYS))
model = genai.GenerativeModel('gemini-1.5-flash')


def determine_category_and_format_text(message: str, category_enum: list[str] = None) -> TextRecognitionResponse:
    if category_enum is None:
        category_enum = list(AITasksCategories.__members__.keys())

    logger.debug(f'Sending message to genai: {message}')

    prompt = 'Determine what categories (maximum 3) this text can be and add punctuation.'

    # noinspection PyTypeChecker
    response_schema = Schema(
        type_=Type.OBJECT,
        properties=dict(
            category_predictions=Schema(
                type_=Type.ARRAY,
                items=Schema(
                    type_=Type.STRING,
                    enum=category_enum,
                ),
            ),
            text=Schema(
                type_=Type.STRING,
            ),
        ),
        required=[
            'category_predictions',
            'text',
        ],
    )

    result = None
    error_message = None
    time_start = time()
    try:
        result = model.generate_content(
            f'{prompt}\n\n{message}',
            generation_config=genai.GenerationConfig(
                response_mime_type='application/json',
                response_schema=response_schema,
            ),
        )
        logger.debug(f'Genai result: {result}')
        result = result.text
    except Exception as e:  # noqa
        logger.exception(f'Error generating content from genai: {e}')
        error_message = str(e)

    time_spent = time() - time_start

    response = TextRecognitionResponse(
        prompt=prompt,
        response=result,
        text=message,
        category=AIMessageCategories.TEXT_RECOGNITION.value[0],
        time_spent=time_spent,
        error_message=error_message,
        is_successful=not error_message,
    )

    if result:
        response.text_recognition = TextRecognition.model_validate_json(result)

        if response.text_recognition.category_predictions:
            response.text_recognition.category_predictions = list(set(response.text_recognition.category_predictions))

    return response


def transcribe_using_openai(file_path: Path) -> VoiceRecognitionResponse:
    logger.debug(f'Transcribing file {file_path} using OpenAI')
    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
    )

    time_start = time()
    audio_file = Path.open(file_path, 'rb')
    result = None
    error_message = None
    try:
        transcription = client.audio.transcriptions.create(
            model='whisper-1',
            file=audio_file,
        )
        result = transcription.text
    except Exception as e:  # noqa
        logger.exception(f'Error transcribing audio file {file_path} using OpenAI: {e}')
        error_message = str(e)

    time_spent = time() - time_start

    return VoiceRecognitionResponse(
        prompt='Voice recognition using OpenAI',
        response=result,
        text=str(file_path),
        category=AIMessageCategories.VOICE_RECOGNITION.value[0],
        time_spent=time_spent,
        error_message=error_message,
        is_successful=not error_message,
        text_recognition=result,
    )


def transcribe_using_genai(file_path: Path, mime_type: str = None) -> VoiceRecognitionResponse:
    # Configure generative AI model

    # Upload file and generate content
    logger.debug(f'Sending file to genai {file_path}')
    time_start = time()
    result = None
    error_message = None
    try:
        file = genai.upload_file(file_path, mime_type=mime_type)
        if not file:
            raise ValueError('Failed to upload file to genai')
    except Exception as e:  # noqa
        logger.exception(f'Error uploading file to genai: {e}')
        return  # noqa

    logger.debug(f'Generating content for file {file_path}')
    prompt = (
        'Transcribe the audio to text, correct grammar, and add punctuation.'
        ' Remove filler words and stutters such as "Э", "ммм", and similar sounds.'
    )
    try:
        result = model.generate_content(
            [
                file,
                prompt,
            ],
        )
        result = result.text
    except Exception as e:  # noqa
        logger.exception(f'Error generating content from genai: {e}')
        error_message = str(e)

    time_spent = time() - time_start

    return VoiceRecognitionResponse(
        prompt=prompt,
        response=result,
        text=str(file_path),
        category=AIMessageCategories.VOICE_RECOGNITION.value[0],
        time_spent=time_spent,
        error_message=error_message,
        is_successful=not error_message,
        text_recognition=result,
    )


def google_translate_speech_to_text(path: Path, language: str) -> VoiceRecognitionResponse:
    """
    Transcribes an audio file at the given path to text and writes the transcribed text to the output file.
    """
    file_path = Path(path)

    time_start = time()
    result = None
    error_message = None
    try:
        if file_path.suffix == '.wav':
            wav_file = str(file_path)
        elif file_path.suffix in ('.mp3', '.m4a', '.ogg', '.flac', '.oga'):
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
            result = str(text)
    except Exception as e:  # noqa
        logger.exception(f'Error generating content from genai: {e}')
        error_message = str(e)

    time_spent = time() - time_start

    return VoiceRecognitionResponse(
        prompt='Voice recognition using Google Speech Recognition',
        response=result,
        text=str(file_path) + f' (language: {language})',
        category=AIMessageCategories.VOICE_RECOGNITION.value[0],
        time_spent=time_spent,
        error_message=error_message,
        is_successful=not error_message,
        text_recognition=result,
    )


def parse_reminder(message: str) -> ReminderRecognitionResponse:
    logger.debug(f'Sending message to genai: {message}')

    prompt = 'Parse the reminder and extract all data.'

    # noinspection PyTypeChecker
    response_schema = Schema(
        type_=Type.OBJECT,
        properties=dict(
            title=Schema(
                type_=Type.STRING,
            ),
            message=Schema(
                type_=Type.STRING,
            ),
            description=Schema(
                type_=Type.STRING,
            ),
            crontab_string=Schema(
                type_=Type.STRING,
            ),
        ),
        required=[
            'title',
            'message',
            'crontab_string',
        ],
    )

    result = None
    error_message = None
    time_start = time()
    try:
        result = model.generate_content(
            f'{prompt}\n\n{message}',
            generation_config=genai.GenerationConfig(
                response_mime_type='application/json',
                response_schema=response_schema,
            ),
        )
        logger.debug(f'Genai result: {result}')
        result = result.text
    except Exception as e:  # noqa
        logger.exception(f'Error generating content from genai: {e}')
        error_message = str(e)

    time_spent = time() - time_start

    response = ReminderRecognitionResponse(
        prompt=prompt,
        response=result,
        text=message,
        category=AIMessageCategories.TEXT_RECOGNITION.value[0],
        time_spent=time_spent,
        error_message=error_message,
        is_successful=not error_message,
    )

    if result:
        response.text_recognition = ReminderRecognition.model_validate_json(result)

    return response
