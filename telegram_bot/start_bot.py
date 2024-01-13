from aiogram import Dispatcher

from telegram_bot.handlers import router
from telegram_bot.loader import dp, bot
from telegram_bot.middlewares import setup_middleware


def initialize_bot() -> Dispatcher:
    dp.include_router(router)

    setup_middleware(dp)

    return dp


async def start_polling() -> None:
    _dp = initialize_bot()
    await _dp.start_polling(bot)
