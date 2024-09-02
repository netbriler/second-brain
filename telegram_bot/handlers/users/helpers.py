import contextlib
from typing import NoReturn

from aiogram import Router
from aiogram.types import CallbackQuery, Message, ReactionTypeEmoji
from django.utils.translation import gettext as _

from telegram_bot.keyboards.default.default import get_default_markup
from telegram_bot.tasks import determine_category_task
from users.models import User

router = Router(name=__name__)


@router.message()
async def _default_menu(message: Message, user: User) -> NoReturn:
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

    # await message.answer(_('Choose an action from the menu 👇'), reply_markup=get_default_markup(user))


@router.callback_query()
async def _default_menu(callback_query: CallbackQuery, user: User) -> NoReturn:
    await callback_query.answer(_('Unknown action'))
    await callback_query.message.answer(_('Choose an action from the menu 👇'), reply_markup=get_default_markup(user))

    with contextlib.suppress(Exception):
        await callback_query.message.delete()


@router.message_reaction()
async def _echo_reaction(message: Message) -> NoReturn:
    pass
