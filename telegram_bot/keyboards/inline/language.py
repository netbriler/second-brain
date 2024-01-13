from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.conf import settings


def get_language_inline_markup():
    builder = InlineKeyboardBuilder()

    for code, title in settings.LANGUAGES:
        builder.button(text=title, callback_data=f'lang_{code}')

    builder.adjust(1)

    return builder.as_markup()
