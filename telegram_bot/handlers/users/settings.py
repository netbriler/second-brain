import re
from typing import NoReturn

from aiogram import Router, Bot
from aiogram.filters import or_f, Command
from aiogram.types import CallbackQuery, Message
from django.utils.translation import gettext as _, override

from telegram_bot.commands.admin import set_admin_commands
from telegram_bot.commands.default import set_user_commands
from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.filters.regexp import Regexp
from telegram_bot.keyboards.default.default import get_default_markup
from telegram_bot.keyboards.inline.language import get_language_inline_markup
from users.models import User

router = Router(name=__name__)


@router.callback_query(
    Regexp(r'^lang_(\w\w)$')
)
async def _change_language(callback_query: CallbackQuery, user: User, regexp: re.Match, bot: Bot) -> NoReturn:
    language = regexp.group(1)

    user.language_code = language
    await user.asave(
        update_fields=(
            'language_code',
        )
    )

    with override(user.language_code):
        await callback_query.message.answer(
            _(
                'Language changed successfully\n'
                'Press /help to find out how I can help you'
            ),
            reply_markup=get_default_markup(user)
        )
        await callback_query.message.delete()

        await set_admin_commands(bot, user.telegram_id, language) if user.is_superuser else await set_user_commands(
            bot, user.telegram_id, language
        )


@router.message(
    or_f(
        I18nText('Settings 🛠'),
        Command(
            commands=['lang', 'settings']
        )
    )
)
async def _settings(message: Message) -> NoReturn:
    text = _('Choose your language')

    await message.answer(text, reply_markup=get_language_inline_markup())
