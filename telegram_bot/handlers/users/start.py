from aiogram import Router, Bot
from aiogram.filters import CommandStart, Command, or_f
from aiogram.types import Message
from django.utils.translation import gettext as _

from telegram_bot.commands.admin import set_admin_commands, get_admin_commands
from telegram_bot.commands.default import get_default_commands
from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.keyboards.inline.language import get_language_inline_markup
from users.models import User

router = Router(name=__name__)


@router.message(CommandStart())
async def _start(message: Message, user: User, bot: Bot):
    if user.is_superuser:
        await set_admin_commands(
            bot=bot,
            user_id=user.telegram_id,
            commands_lang=user.language_code
        )

    text = _(
        'Hi {full_name}!\n'
        'Choose your language_code'
    ).format(full_name=message.from_user.full_name)

    await message.answer(text, reply_markup=get_language_inline_markup())


@router.message(
    or_f(
        I18nText('Help 🆘'),
        Command(
            commands=['help']
        )
    )
)
async def _help(message: Message, user: User):
    commands = get_admin_commands(user.language_code) if user.is_superuser else get_default_commands(user.language_code)

    text = _('Help 🆘') + '\n\n'
    for command in commands:
        text += f'{command.command} - {command.description}\n'

    await message.answer(text)
