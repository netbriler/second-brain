from aiogram.utils.keyboard import ReplyKeyboardBuilder
from django.utils.translation import gettext as _
from telebot.types import ReplyKeyboardMarkup


def get_learning_session_keyboard(has_next_lesson: bool = True) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.button(text=_('Stop learning session 🛑'))
    if has_next_lesson:
        builder.button(text=_('Finish current lesson ✅'))

    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)
