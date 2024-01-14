from typing import NoReturn

from aiogram import Bot
from aiogram import Dispatcher

from telegram_bot.commands.default import set_default_commands
from telegram_bot.handlers import router
from telegram_bot.loader import dp
from telegram_bot.middlewares import setup_middleware


def initialize() -> Dispatcher:
    dp.include_router(router)

    setup_middleware(dp)

    return dp


async def on_startup(bot: Bot) -> NoReturn:
    await set_default_commands(bot)


async def start_polling() -> NoReturn:
    from telegram_bot.loader import bot

    _dp = initialize()
    _dp.startup.register(on_startup)
    await _dp.start_polling(bot)
