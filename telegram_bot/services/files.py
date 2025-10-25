import json  # noqa: I001
from typing import NoReturn

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.types import ForceReply, InlineKeyboardMarkup
from aiogram.types import Message as AiogramMessage
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from django.utils.translation import gettext as _
from telebot import TeleBot

from telegram_bot.constants import MessageRoles
from telegram_bot.models import File, Message
from users.models import User
from utils.logging import logger


def generate_file_text(file: File) -> str:
    raw_data = ''
    for key, value in file.raw_data.items():
        raw_data += f'<b>{key.title().replace("_", " ")}</b>: <code>{value}</code>\n'

    return _(
        'New file uploaded:\n'
        '<b>File type</b>: <code>{content_type}</code>\n'
        '<b>File ID</b>: <code>{file_id}</code>\n'
        '<b>Uploaded by</b>: <a href="tg://user?id={uploaded_by_id}">{uploaded_by}</a>\n'
        '\n<b>Raw Data</b>:\n{raw_data}',
    ).format(
        content_type=file.get_content_type_display(),
        file_id=file.file_id,
        uploaded_by=str(file.uploaded_by),
        uploaded_by_id=file.uploaded_by.telegram_id,
        raw_data=raw_data,
    )


async def send_file_to_user(
    bot: Bot,
    file: File,
    user: User,
    send_file_info: bool = False,
    caption: str = None,
    reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply = None,
    document_as_image: bool = False,
) -> tuple[int, int]:
    if file.content_type == ContentType.AUDIO:
        message = await bot.send_audio(
            user.telegram_id,
            file.file_id,
            caption=caption,
            reply_markup=reply_markup,
        )
    elif file.content_type == ContentType.DOCUMENT:
        if document_as_image and file.mime_type and file.mime_type.startswith('image/'):
            message = await bot.send_photo(
                user.telegram_id,
                file.file_id,
                caption=caption,
                reply_markup=reply_markup,
            )
        else:
            message = await bot.send_document(
                user.telegram_id,
                file.file_id,
                caption=caption,
                reply_markup=reply_markup,
            )
    elif file.content_type == ContentType.PHOTO:
        message = await bot.send_photo(
            user.telegram_id,
            file.file_id,
            caption=caption,
            reply_markup=reply_markup,
        )
    elif file.content_type == ContentType.STICKER:
        message = await bot.send_sticker(
            user.telegram_id,
            file.file_id,
            reply_markup=reply_markup,
        )
    elif file.content_type == ContentType.VIDEO:
        message = await bot.send_video(
            user.telegram_id,
            file.file_id,
            caption=caption,
            reply_markup=reply_markup,
        )
    elif file.content_type == ContentType.VIDEO_NOTE:
        message = await bot.send_video_note(
            user.telegram_id,
            file.file_id,
            reply_markup=reply_markup,
        )
    elif file.content_type == ContentType.VOICE:
        message = await bot.send_voice(
            user.telegram_id,
            file.file_id,
            reply_markup=reply_markup,
        )
    else:
        message = await bot.send_message(user.telegram_id, _('Unknown content type'))

    message2_id = None
    if send_file_info:
        text = generate_file_text(file)
        message2 = await bot.send_message(user.telegram_id, text, reply_to_message_id=message.message_id)
        message2_id = message2.message_id

    return message.message_id, message2_id


def sync_send_file_to_user(
    bot: TeleBot,
    file: File,
    user: User,
    send_file_info: bool = False,
    caption: str = None,
) -> tuple[int, int]:
    if file.content_type == ContentType.AUDIO:
        message = bot.send_audio(
            user.telegram_id,
            file.file_id,
            caption=caption,
        )
    elif file.content_type == ContentType.DOCUMENT:
        message = bot.send_document(
            user.telegram_id,
            file.file_id,
            caption=caption,
        )
    elif file.content_type == ContentType.PHOTO:
        message = bot.send_photo(
            user.telegram_id,
            file.file_id,
            caption=caption,
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
            caption=caption,
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
        )
    else:
        message = bot.send_message(user.telegram_id, _('Unknown content type'))

    message2_id = None
    if send_file_info:
        text = generate_file_text(file)
        message2 = bot.send_message(user.telegram_id, text, reply_to_message_id=message.message_id)
        message2_id = message2.message_id
    return message.message_id, message2_id


async def save_file(message: AiogramMessage, user: User) -> NoReturn:
    logger.debug(f'User {user} uploaded file {message.content_type}')
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

    file, created = await File.objects.aupdate_or_create(
        content_type=message.content_type,
        file_id=file_id,
        defaults={
            'raw_data': data,
            'file_unique_id': data.get('file_unique_id', None),
            'mime_type': data.get('mime_type', None),
            'caption': message.caption,
        },
    )

    if created:
        file.uploaded_by = user
        await file.asave(
            update_fields=[
                'uploaded_by',
            ],
        )

    return file


async def create_message(
    message_id: int,
    chat_id: int,
    user: User,
    text: str,
    raw_data: dict,
    role: MessageRoles = None,
    file: File = None,
) -> Message:
    if not role:
        role = MessageRoles.SIMPLE

    role = role.value[0] if isinstance(role, MessageRoles) else role

    return await Message.objects.acreate(
        message_id=message_id,
        chat_id=chat_id,
        text=text,
        raw_data=raw_data,
        role=role,
        user=user,
        file=file,
    )


def get_message_duration(message: AiogramMessage) -> int:
    if message.content_type == ContentType.AUDIO:
        return message.audio.duration
    elif message.content_type == ContentType.VIDEO:
        return message.video.duration
    elif message.content_type == ContentType.VOICE:
        return message.voice.duration
    elif message.content_type == ContentType.VIDEO_NOTE:
        return message.video_note.duration

    raise ValueError('Unknown content type')
