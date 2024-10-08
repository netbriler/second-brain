from typing import NoReturn

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat
from django.utils.translation import gettext as _
from django.utils.translation import override

from .default import get_default_commands


def get_admin_commands(lang: str = 'en', with_categories: bool = False) -> list[BotCommand | str]:
    commands = get_default_commands(lang)

    with override(lang):
        commands.extend(
            [
                _('\n<b>Admin commands 👑</b>'),
                BotCommand(command='/user', description=_('get user info')),
                BotCommand(command='/export_users', description=_('export users to csv')),
                BotCommand(command='/count_users', description=_('count users who contacted the bot')),
                BotCommand(
                    command='/count_active_users',
                    description=_("count active users (who didn't block the bot)"),
                ),
                _('\n<b>File commands 📁</b>'),
                BotCommand(command='/file', description=_('get file')),
                BotCommand(command='/upload_files', description=_('upload files')),
                _('\n<b>Helpers commands 🛠</b>'),
                BotCommand(command='/dump_state', description=_('dump state')),
                BotCommand(command='/clear_state', description=_('clear state')),
            ],
        )

        if not with_categories:
            return [c for c in commands if isinstance(c, BotCommand)]

        return commands


async def set_admin_commands(bot: Bot, user_id: int, commands_lang: str) -> NoReturn:
    await bot.set_my_commands(get_admin_commands(commands_lang), scope=BotCommandScopeChat(chat_id=user_id))
