from typing import NoReturn

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from django.conf import settings

from telegram_bot.commands.default import set_default_commands
from telegram_bot.handlers import router
from telegram_bot.middlewares import setup_middleware

dp = Dispatcher()

bot = Bot(
    settings.TELEGRAM_BOT_TOKEN,
    parse_mode=ParseMode.HTML,
    disable_web_page_preview=True
)


async def on_startup(bot: Bot) -> NoReturn:
    print('Starting bot...')
    await set_default_commands(bot)
    await bot.set_webhook(
        f"{settings.TELEGRAM_BASE_WEBHOOK_URL}{settings.TELEGRAM_WEBHOOK_PATH}",
        secret_token=settings.TELEGRAM_WEBHOOK_SECRET
    )


def initialize() -> Dispatcher:
    dp.include_router(router)

    setup_middleware(dp)
    dp.startup.register(on_startup)

    return dp


dispatcher = initialize()


async def start_polling() -> NoReturn:
    await dispatcher.start_polling(bot)


def start_webhook() -> NoReturn:
    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=settings.TELEGRAM_WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host=settings.TELEGRAM_WEB_SERVER_HOST, port=settings.TELEGRAM_WEB_SERVER_PORT)
