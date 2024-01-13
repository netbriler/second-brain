from aiogram import Bot
from aiogram.types import BotCommandScopeDefault, BotCommandScopeChat, BotCommand
from django.conf import settings
from django.utils.translation import override, gettext as _


def get_default_commands(lang: str = 'en') -> list[BotCommand]:
    with override(lang):
        commands = [
            BotCommand(command='/start', description=_('start bot')),
            BotCommand(command='/help', description=_('how it works?')),
            BotCommand(command='/lang', description=_('change language')),
            BotCommand(command='/settings', description=_('open bot settings')),
        ]

        return commands


async def set_default_commands(bot: Bot):
    await bot.set_my_commands(get_default_commands(), scope=BotCommandScopeDefault())

    for lang, _ in settings.LANGUAGES:
        await bot.set_my_commands(get_default_commands(lang), scope=BotCommandScopeDefault(), language_code=lang)


async def set_user_commands(bot: Bot, user_id: int, commands_lang: str):
    await bot.set_my_commands(get_default_commands(commands_lang), scope=BotCommandScopeChat(chat_id=user_id))
