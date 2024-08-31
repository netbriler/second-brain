from typing import NoReturn

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from django.conf import settings

from telegram_bot.commands.default import set_default_commands
from telegram_bot.handlers import router
from telegram_bot.middlewares import setup_middleware
from utils.logging import logger

from .loader import default_bot

dp = Dispatcher()

dp.include_router(router)
setup_middleware(dp)


async def on_startup(bot: Bot) -> NoReturn:
    await set_default_commands(bot)
    bot_username = (await bot.me()).username
    logger.info(f'Bot @{bot_username} started')


async def on_shutdown(bot: Bot) -> NoReturn:
    bot_username = (await bot.me()).username
    logger.info(f'Bot @{bot_username} stopped')
    await bot.delete_webhook()


async def on_startup_polling(bot: Bot) -> NoReturn:
    await on_startup(bot)


async def start_polling() -> NoReturn:
    await default_bot.delete_webhook()
    dp.startup.register(on_startup_polling)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(default_bot)


async def on_startup_webhook(bot: Bot) -> NoReturn:
    await on_startup(bot)
    webhook_url = f'{settings.TELEGRAM_BASE_WEBHOOK_URL}{settings.TELEGRAM_WEBHOOK_PATH}'
    await bot.set_webhook(
        webhook_url,
        secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
    )
    logger.info(f'Webhook set to {webhook_url}')


def start_webhook() -> NoReturn:
    dp.startup.register(on_startup_webhook)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=default_bot,
        secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=settings.TELEGRAM_WEBHOOK_PATH)

    setup_application(app, dp, bot=default_bot)

    web.run_app(app, host=settings.TELEGRAM_WEB_SERVER_HOST, port=settings.TELEGRAM_WEB_SERVER_PORT)
