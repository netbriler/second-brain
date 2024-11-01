from aiogram.utils.keyboard import ReplyKeyboardBuilder
from django.utils.translation import gettext as _


def get_cancel_markup(input_field_placeholder: str = None):
    builder = ReplyKeyboardBuilder()

    builder.button(text=_('Cancel ❌'))

    return builder.as_markup(resize_keyboard=True, input_field_placeholder=input_field_placeholder)
