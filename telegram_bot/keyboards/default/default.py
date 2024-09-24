from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from django.utils.translation import gettext as _


def get_default_markup(user):
    builder = ReplyKeyboardBuilder()

    builder.button(text=_('Help 🆘'))
    builder.button(text=_('Settings 🛠'))

    if user.is_superuser:
        builder.button(text=_('Upload file 📁'))
        builder.button(text=_('Export users 📁'))
        builder.button(text=_('Count users 👥'))
        builder.button(text=_('Count active users 👥'))
        builder.button(text=_('Courses 📚'))

    if len(builder.export()) > 1:
        return ReplyKeyboardRemove()

    builder.adjust(2, 1)

    return builder.as_markup(resize_keyboard=True)
