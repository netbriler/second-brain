from typing import NoReturn

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import override


def get_default_commands(lang: str = 'en', with_categories: bool = False) -> list[BotCommand | str]:
    with override(lang):
        commands = [
            BotCommand(command='/start', description=_('start bot')),
            BotCommand(command='/help', description=_('how it works?')),
            BotCommand(command='/lang', description=_('change language')),
            BotCommand(command='/settings', description=_('open bot settings')),
            _('\nLearning commands 📚'),
            BotCommand(command='/stop_learning_session', description=_('stop learning session')),
        ]

        if not with_categories:
            return [c for c in commands if isinstance(c, BotCommand)]

        return commands


async def set_default_commands(bot: Bot) -> NoReturn:
    await bot.set_my_commands(get_default_commands(), scope=BotCommandScopeDefault())

    for lang in settings.LANGUAGES:
        await bot.set_my_commands(get_default_commands(lang[0]), scope=BotCommandScopeDefault(), language_code=lang[0])


async def set_user_commands(bot: Bot, user_id: int, commands_lang: str) -> NoReturn:
    await bot.set_my_commands(get_default_commands(commands_lang), scope=BotCommandScopeChat(chat_id=user_id))
