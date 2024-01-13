from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from django.utils.translation import gettext as _

from telegram_bot.commands import get_default_commands, set_admin_commands, get_admin_commands
from telegram_bot.keyboards.inline import get_language_inline_markup
from users.models import User

router = Router(name=__name__)


@router.message(CommandStart())
async def _start(message: Message, user: User):
    if user.is_superuser:
        await set_admin_commands(user.telegram_id)

    text = _(
        'Hi {full_name}!\n'
        'Choose your language_code'
    ).format(full_name=message.from_user.full_name)

    await message.answer(text, reply_markup=get_language_inline_markup())


# @router.message(i18n_text='Help 🆘')
@router.message(
    Command(
        commands=['help']
    )
)
async def _help(message: Message, user: User):
    commands = get_admin_commands() if user.is_superuser else get_default_commands()

    text = _('Help 🆘') + '\n\n'
    for command in commands:
        text += f'{command.command} - {command.description}\n'

    await message.answer(text)
