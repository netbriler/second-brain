from aiogram.types import BotCommandScopeChat, BotCommand
from django.utils.translation import gettext as _

from .default import get_default_commands
from ..loader import bot


def get_admin_commands() -> list[BotCommand]:
    commands = get_default_commands()

    commands.extend(
        [
            BotCommand(command='/export_users', description=_('export users to csv')),
            BotCommand(command='/count_users', description=_('count users who contacted the bot')),
            BotCommand(
                command='/count_active_users',
                description=_('count active users (who didn\'t block the bot)')
            ),
        ]
    )

    return commands


async def set_admin_commands(user_id: int):
    await bot.set_my_commands(get_admin_commands(), scope=BotCommandScopeChat(chat_id=user_id))
