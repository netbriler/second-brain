import json
from typing import NoReturn

from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.types import Message
from django.utils.translation import gettext as _

from telegram_bot.filters.admin import IsAdmin
from telegram_bot.models import File
from users.models import User

router = Router(name=__name__)


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
async def _upload_file(message: Message, user: User) -> NoReturn:
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

    text = _(
        'New file uploaded:\n'
        '<b>File type</b>: {content_type}\n'
        '<b>Title</b>: {title}\n'
        '<b>File ID</b>: {file_id}\n'
        '<b>Thumbnail ID</b>: {thumbnail_id}\n'
        '<b>Uploaded by</b>: <a href="tg://user?id={uploaded_by_id}">{uploaded_by}</a>\n',
    ).format(
        content_type=file.get_content_type_display(),
        title=file.title,
        file_id=file.file_id,
        thumbnail_id=file.thumbnail_id,
        uploaded_by=str(file.uploaded_by),
        uploaded_by_id=file.uploaded_by.telegram_id,
    )

    await message.answer(text, parse_mode='HTML')
