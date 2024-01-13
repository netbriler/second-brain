from aiogram import Router
from aiogram.types import Message, CallbackQuery
from django.utils.translation import gettext as _

from telegram_bot.keyboards.default import get_default_markup
from users.models import User

router = Router(name=__name__)


@router.message()
async def _default_menu(message: Message, user: User):
    await message.answer(_('Choose an action from the menu 👇'), reply_markup=get_default_markup(user))


@router.callback_query()
async def _default_menu(callback_query: CallbackQuery, user: User):
    await callback_query.message.edit_text(_('Choose an action from the menu 👇'), reply_markup=get_default_markup(user))
