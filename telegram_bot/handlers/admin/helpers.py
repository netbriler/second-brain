from typing import NoReturn

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from django.utils.translation import gettext as _

from telegram_bot.filters.admin import IsAdmin

router = Router(name=__name__)


@router.message(
    IsAdmin(),
    Command(commands=['dump_state']),
)
async def _dump_state(message: Message, state: FSMContext) -> NoReturn:
    state_form = await state.get_state()
    if not state_form:
        return await message.answer(_('No state'))

    data = await state.get_data()
    text = f'<b>Current state:</b> <code>{state_form}</code>\n\n<b>Data:</b>\n'
    for key, value in data.items():
        text += f'<b>{key}</b>: <code>{value}</code>\n'

    await message.answer(text)


@router.message(
    IsAdmin(),
    Command(commands=['clear_state']),
)
async def _clear_state(message: Message, state: FSMContext) -> NoReturn:
    await state.clear()
    await message.answer(_('State cleared'))
