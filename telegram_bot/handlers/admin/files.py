import re
from typing import NoReturn

from aiogram import Bot, F, Router
from aiogram.enums import ContentType
from aiogram.filters import Command, CommandObject, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from django.utils.translation import gettext as _

from telegram_bot.filters.admin import IsAdmin
from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.keyboards.default.cancel import get_cancel_markup
from telegram_bot.models import File
from telegram_bot.services.files import save_file, send_file_to_user
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


class FilesAddForm(StatesGroup):
    add_file = State()


@router.message(
    IsAdmin(),
    or_f(
        I18nText('Upload file 📁'),
        Command(commands=['upload_files']),
    ),
)
async def _upload_files(message: Message, state: FSMContext) -> NoReturn:
    await state.set_state(FilesAddForm.add_file)

    await message.answer(_('Send me a something to upload'), reply_markup=get_cancel_markup())


@router.message(
    IsAdmin(),
    FilesAddForm.add_file,
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
    file = await save_file(
        message=message,
        user=user,
    )

    await send_file_to_user(bot, file, user)
