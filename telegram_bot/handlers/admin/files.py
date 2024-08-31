import json
import random
import re
from typing import NoReturn

import google.generativeai as genai
from aiogram import Bot, F, Router
from aiogram.enums import ContentType
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from django.utils.translation import gettext as _

from telegram_bot.filters.admin import IsAdmin
from telegram_bot.models import File
from telegram_bot.services.files import send_file_to_user
from users.models import User

router = Router(name=__name__)


@router.message(
    IsAdmin(),
    Command(re.compile(r'file[\s|_]?([\w]*)', re.IGNORECASE)),
)
async def _file(message: Message, bot: Bot, command: CommandObject, user: User) -> NoReturn:
    search_file = command.regexp_match.group(1) or command.args
    if not search_file:
        return await message.answer(_('Usage:\n/file [file_id]'))

    file = await File.objects.filter(file_id__iexact=search_file).select_related('uploaded_by').afirst()

    if not file:
        await message.answer(_('file not found'))
        return NoReturn

    await send_file_to_user(bot, file, user)


@router.message(
    IsAdmin(),
    F.content_type.in_(
        {
            ContentType.AUDIO,
            ContentType.DOCUMENT,
            ContentType.PHOTO,
            ContentType.STICKER,
            ContentType.VIDEO,
            ContentType.VIDEO_NOTE,
            ContentType.VOICE,
        },
    ),
)
async def _upload_file(message: Message, user: User, bot: Bot) -> NoReturn:
    raw_json = None
    if message.content_type == ContentType.AUDIO:
        raw_json = message.audio.model_dump_json()
    elif message.content_type == ContentType.DOCUMENT:
        raw_json = message.document.model_dump_json()
    elif message.content_type == ContentType.PHOTO:
        raw_json = message.photo[-1].model_dump_json()
    elif message.content_type == ContentType.STICKER:
        raw_json = message.sticker.model_dump_json()
    elif message.content_type == ContentType.VIDEO:
        raw_json = message.video.model_dump_json()
    elif message.content_type == ContentType.VIDEO_NOTE:
        raw_json = message.video_note.model_dump_json()
    elif message.content_type == ContentType.VOICE:
        raw_json = message.voice.model_dump_json()

        if message.voice:
            api_keys = ['AIzaSyDsGM7Bv0S2oOJHBWUthvl8GF8J21oq0vg', 'AIzaSyBgyocfylSsMreU_2Qn7PBIX7HDlXsqzz0']
            genai.configure(api_key=random.choice(api_keys))

            file = await message.bot.get_file(message.voice.file_id)
            file_path = file.file_path

            destination = f'temp/{file.file_id}.ogg'
            await message.bot.download_file(file_path, destination=destination)

            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                result = model.generate_content(
                    [genai.upload_file(destination), '\n\n', 'Transcribe audio'],
                )
                await message.reply(result.text)
            except Exception as e:  # noqa
                await message.answer('Something went wrong, try again later')

    data = json.loads(raw_json)
    file_id = data.get('file_id', None)
    if not file_id:
        return NoReturn

    if title := data.get('title', data.get('file_name', None)):
        title = title.encode('utf-16', 'surrogatepass').decode('utf-16')

    thumbnail_id = None
    if thumbnail := data.get('thumbnail', data.get('thumb', None)):
        thumbnail_id = thumbnail.get('file_id', None)

    file, created = await File.objects.aupdate_or_create(
        content_type=message.content_type,
        file_id=file_id,
        defaults={
            'title': title,
            'thumbnail_id': thumbnail_id,
            'raw_data': data,
        },
    )

    if created:
        file.uploaded_by = user
        await file.asave(
            update_fields=[
                'uploaded_by',
            ],
        )

    await send_file_to_user(bot, file, user)
