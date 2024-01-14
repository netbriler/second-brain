from typing import NoReturn

from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart, or_f
from aiogram.types import Message
from django.utils.translation import gettext as _

from telegram_bot.commands.admin import set_admin_commands
from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.keyboards.inline.language import get_language_inline_markup
from telegram_bot.messages import get_help_text
from users.models import User

router = Router(name=__name__)


@router.message(CommandStart())
async def _start(message: Message, user: User, bot: Bot) -> NoReturn:
    if user.is_superuser:
        await set_admin_commands(
            bot=bot,
            user_id=user.telegram_id,
            commands_lang=user.language_code,
        )

    text = _(
        'Hi {full_name}!\nChoose your language_code',
    ).format(full_name=message.from_user.full_name)

    await message.answer(text, reply_markup=get_language_inline_markup())


@router.message(
    or_f(
        I18nText('Help 🆘'),
        Command(
            commands=['help'],
        ),
    ),
)
async def _help(message: Message, user: User) -> NoReturn:
    text = get_help_text(user)

    await message.answer(text)
