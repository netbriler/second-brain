from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from django.conf import settings
from pyrogram import Client
from telebot import TeleBot

default_bot = (
    Bot(
        settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )
    if settings.TELEGRAM_BOT_TOKEN
    else None
)


def get_sync_bot() -> TeleBot:
    return TeleBot(
        settings.TELEGRAM_BOT_TOKEN,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


def get_pyrogram_bot() -> Client:
    client = Client(
        'bot',
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        api_id=settings.TELEGRAM_API_ID,
        api_hash=settings.TELEGRAM_API_HASH,
    )
    is_started = False

    def start():
        nonlocal is_started
        if not is_started:
            client.start()
            is_started = True
        return client

    return start()
