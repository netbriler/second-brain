from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_language_inline_markup():
    builder = InlineKeyboardBuilder()

    builder.button(text='🇺🇸 English', callback_data='lang_en')
    builder.button(text='🇷🇺 Русский', callback_data='lang_ru')
    builder.button(text='🇺🇦 Українська', callback_data='lang_uk')

    builder.adjust(1)

    return builder.as_markup()
