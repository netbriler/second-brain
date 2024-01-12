from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from django.conf import settings

dp = Dispatcher()

bot = Bot(
    settings.TELEGRAM_BOT_TOKEN,
    parse_mode=ParseMode.HTML,
    disable_web_page_preview=True
)
