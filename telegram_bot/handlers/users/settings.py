import re
from typing import NoReturn

from aiogram import Bot, Router
from aiogram.filters import Command, or_f
from aiogram.types import CallbackQuery, Message
from django.utils.translation import gettext as _
from django.utils.translation import override

from telegram_bot.commands.admin import set_admin_commands
from telegram_bot.commands.default import set_user_commands
from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.filters.regexp import Regexp
from telegram_bot.keyboards.inline.help import get_help_inline_markup
from telegram_bot.keyboards.inline.language import get_language_inline_markup
from telegram_bot.services.messages import get_help_text
from users.models import User

router = Router(name=__name__)


@router.callback_query(
    Regexp(r'^lang_(\w\w)$'),
)
async def _change_language(callback_query: CallbackQuery, user: User, regexp: re.Match, bot: Bot) -> NoReturn:
    language = regexp.group(1)

    user.language_code = language
    await user.asave(
        update_fields=('language_code',),
    )

    with override(user.language_code):
        await callback_query.answer(
            _('Language changed to {language}').format(language=user.language_code),
        )
        text = get_help_text(user)
        await callback_query.message.answer(text, reply_markup=get_help_inline_markup())

        await set_admin_commands(
            callback_query.message.bot,
            user.telegram_id,
            user.language_code,
        ) if user.is_superuser else await set_user_commands(
            callback_query.message.bot,
            user.telegram_id,
            user.language_code,
        )

    await callback_query.message.delete()


@router.message(
    or_f(
        I18nText('Settings 🛠'),
        Command(
            commands=['lang', 'settings'],
        ),
    ),
)
async def _settings(message: Message) -> NoReturn:
    text = _('Choose your language')

    await message.answer(text, reply_markup=get_language_inline_markup())
