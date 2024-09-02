import random
from pathlib import Path

import google.generativeai as genai
import speech_recognition as sr
from google.ai.generativelanguage_v1beta import Schema, Type
from loguru import logger
from openai import OpenAI
from pydantic import BaseModel
from pydub import AudioSegment

from ai.constants import AIMessageCategories
from app import settings

genai.configure(api_key=random.choice(settings.GOOGLE_GEMINI_API_KEYS))
model = genai.GenerativeModel('gemini-1.5-flash')


class TextRecognition(BaseModel):
    text: str
    category_predictions: list[str]


# noinspection PyTypeChecker
def determine_category_and_format_text(message: str, category_enum: list[str] = None) -> TextRecognition | None:
    if category_enum is None:
        category_enum = list(AIMessageCategories.__members__.keys())

    logger.debug(f'Sending message to genai: {message}')
    result = model.generate_content(
        f'Determine what categories (maximum 3) this text can be and add punctuation.\n\n{message}',
        generation_config=genai.GenerationConfig(
            response_mime_type='application/json',
            response_schema=Schema(
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
            ),
        ),
    )

    logger.debug(f'Genai result: {result}')

    if result.text:
        return TextRecognition.model_validate_json(result.text)


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
