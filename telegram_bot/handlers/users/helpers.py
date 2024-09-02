import contextlib
from typing import NoReturn

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReactionTypeEmoji
from django.utils.translation import gettext as _

from ai.tasks import determine_category_task, transcribe_file_task
from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.keyboards.default.default import get_default_markup
from telegram_bot.services.files import save_file
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

    if message.content_type == ContentType.TEXT:
        determine_category_task.delay(
            chat_id=message.chat.id,
            user_id=user.id,
            message=message.text,
            message_id=message.message_id,
        )

        await message.bot.set_message_reaction(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reaction=[
                ReactionTypeEmoji(emoji='👀'),
            ],
        )
    elif message.content_type == ContentType.VOICE:
        file = await save_file(
            message=message,
            user=user,
        )
        transcribe_file_task.delay(
            chat_id=message.chat.id,
            message_id=message.message_id,
            file_id=file.id,
            user_id=user.id,
        )
    else:
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
