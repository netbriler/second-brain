from aiogram.types import BotCommandScopeDefault, BotCommandScopeChat, BotCommand
from django.utils.translation import gettext as _

from telegram_bot.loader import bot


def get_default_commands() -> list[BotCommand]:
    commands = [
        BotCommand(command='/start', description=_('start bot')),
        BotCommand(command='/help', description=_('how it works?')),
        BotCommand(command='/lang', description=_('change language')),
        BotCommand(command='/settings', description=_('open bot settings')),
    ]

    return commands


async def set_default_commands():
    await bot.set_my_commands(get_default_commands(), scope=BotCommandScopeDefault())

    # for lang in i18n.available_locales:
    #     await bot.set_my_commands(get_default_commands(lang), scope=BotCommandScopeDefault(), language_code=lang)
    #


async def set_user_commands(user_id: int):
    await bot.set_my_commands(get_default_commands(), scope=BotCommandScopeChat(chat_id=user_id))
