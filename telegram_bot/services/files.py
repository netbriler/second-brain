from typing import NoReturn

from aiogram import Bot
from aiogram.enums import ContentType
from django.utils.translation import gettext as _

from telegram_bot.models import File
from users.models import User


async def send_file_to_user(bot: Bot, file: File, user: User) -> NoReturn:
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

    if file.content_type == ContentType.AUDIO:
        message = await bot.send_audio(
            user.telegram_id,
            file.file_id,
            caption=file.title,
        )
    elif file.content_type == ContentType.DOCUMENT:
        message = await bot.send_document(
            user.telegram_id,
            file.file_id,
            caption=file.title,
        )
    elif file.content_type == ContentType.PHOTO:
        message = await bot.send_photo(
            user.telegram_id,
            file.file_id,
            caption=file.title,
        )
    elif file.content_type == ContentType.STICKER:
        message = await bot.send_sticker(
            user.telegram_id,
            file.file_id,
        )
    elif file.content_type == ContentType.VIDEO:
        message = await bot.send_video(
            user.telegram_id,
            file.file_id,
            caption=file.title,
        )
    elif file.content_type == ContentType.VIDEO_NOTE:
        message = await bot.send_video_note(
            user.telegram_id,
            file.file_id,
        )
    elif file.content_type == ContentType.VOICE:
        message = await bot.send_voice(
            user.telegram_id,
            file.file_id,
            caption=file.title,
        )
    else:
        message = await bot.send_message(_('Unknown content type'))

    await bot.send_message(user.telegram_id, text, reply_to_message_id=message.message_id)
