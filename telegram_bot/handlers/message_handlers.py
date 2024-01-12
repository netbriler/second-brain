from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from telegram_bot.loader import dp


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!")
