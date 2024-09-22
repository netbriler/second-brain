import contextlib
import json
from typing import NoReturn

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from django.utils.translation import gettext as _

from telegram_bot.constants import MessageRoles
from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.keyboards.default.default import get_default_markup
from telegram_bot.services.files import create_message, save_file
from users.models import User

router = Router(name=__name__)


@router.message(I18nText('Cancel ❌'))
async def _cancel(message: Message, user: User, state: FSMContext) -> NoReturn:
    await state.clear()
    await message.answer(_('Choose an action from the menu 👇'), reply_markup=get_default_markup(user))


@router.message()
async def _default_menu(message: Message, user: User, state: FSMContext) -> NoReturn:
    if await state.get_state():
        return await _cancel(message, user, state)

    file = None
    role = None
    if message.content_type == ContentType.TEXT:
        role = MessageRoles.TEXT_RECOGNITION
    elif message.content_type in [ContentType.VOICE]:
        role = MessageRoles.VOICE_RECOGNITION
        file = await save_file(
            message=message,
            user=user,
        )

    await create_message(
        message_id=message.message_id,
        chat_id=message.chat.id,
        text=message.text or message.caption or '',
        user=user,
        raw_data=json.loads(message.model_dump_json()),
        role=role,
        file=file,
    )

    if not role:
        return await message.answer(_('Choose an action from the menu 👇'), reply_markup=get_default_markup(user))


@router.callback_query()
async def _default_menu(callback_query: CallbackQuery, user: User) -> NoReturn:
    await callback_query.answer(_('Unknown action'))
    await callback_query.message.answer(_('Choose an action from the menu 👇'), reply_markup=get_default_markup(user))

    with contextlib.suppress(Exception):
        await callback_query.message.delete()


@router.message_reaction()
async def _echo_reaction(message: Message) -> NoReturn:
    pass
