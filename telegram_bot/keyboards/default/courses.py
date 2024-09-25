from aiogram.utils.keyboard import ReplyKeyboardBuilder
from django.utils.translation import gettext as _
from telebot.types import ReplyKeyboardMarkup


def get_learning_session_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.button(text=_('Stop learning session 🛑'))

    return builder.as_markup(resize_keyboard=True)
