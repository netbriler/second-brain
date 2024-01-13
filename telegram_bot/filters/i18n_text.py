from aiogram.filters import Filter
from aiogram.types import Message
from django.conf import settings
from django.utils.translation import gettext as _, override


class I18nText(Filter):
    def __init__(self, i18n_text: str) -> None:
        self.i18n_text = i18n_text

    async def __call__(self, message: Message) -> bool:
        if not isinstance(message, Message):
            return False

        available = {self.i18n_text}
        for lang_code, lang_name in settings.LANGUAGES:
            if lang_code == 'en':
                continue

            with override(lang_code):
                available.add(_(self.i18n_text))

        return message.text in available
