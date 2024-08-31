from aiogram import Bot
from aiogram.enums import ContentType
from django.utils.translation import gettext as _
from telebot import TeleBot

from telegram_bot.models import File
from users.models import User


def generate_file_text(file: File) -> str:
    return _(
        'New file uploaded:\n'
        '<b>File type</b>: {content_type}\n'
        '<b>Title</b>: {title}\n'
        '<b>File ID</b>: {file_id}\n'
        '<b>Thumbnail ID</b>: {thumbnail_id}\n'
        '<b>Uploaded by</b>: <a href="tg://user?id={uploaded_by_id}">{uploaded_by}</a>\n'
        '<code>{raw_data}</code>\n',
    ).format(
        content_type=file.get_content_type_display(),
        title=file.title,
        file_id=file.file_id,
        thumbnail_id=file.thumbnail_id,
        uploaded_by=str(file.uploaded_by),
        uploaded_by_id=file.uploaded_by.telegram_id,
        raw_data=file.raw_data,
    )


async def send_file_to_user(bot: Bot, file: File, user: User) -> tuple[int, int]:
    text = generate_file_text(file)

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
        message = await bot.send_message(user.telegram_id, _('Unknown content type'))

    message2 = await bot.send_message(user.telegram_id, text, reply_to_message_id=message.message_id)
    return message.message_id, message2.message_id


def sync_send_file_to_user(bot: TeleBot, file: File, user: User) -> tuple[int, int]:
    text = generate_file_text(file)

    if file.content_type == ContentType.AUDIO:
        message = bot.send_audio(
            user.telegram_id,
            file.file_id,
            caption=file.title,
        )
    elif file.content_type == ContentType.DOCUMENT:
        message = bot.send_document(
            user.telegram_id,
            file.file_id,
            caption=file.title,
        )
    elif file.content_type == ContentType.PHOTO:
        message = bot.send_photo(
            user.telegram_id,
            file.file_id,
            caption=file.title,
        )
    elif file.content_type == ContentType.STICKER:
        message = bot.send_sticker(
            user.telegram_id,
            file.file_id,
        )
    elif file.content_type == ContentType.VIDEO:
        message = bot.send_video(
            user.telegram_id,
            file.file_id,
            caption=file.title,
        )
    elif file.content_type == ContentType.VIDEO_NOTE:
        message = bot.send_video_note(
            user.telegram_id,
            file.file_id,
        )
    elif file.content_type == ContentType.VOICE:
        message = bot.send_voice(
            user.telegram_id,
            file.file_id,
            caption=file.title,
        )
    else:
        message = bot.send_message(user.telegram_id, _('Unknown content type'))

    message2 = bot.send_message(user.telegram_id, text, reply_to_message_id=message.message_id)

    return message.message_id, message2.message_id
