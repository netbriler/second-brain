import re
from typing import NoReturn

from aiogram.filters import Filter
from aiogram.types import CallbackQuery, InlineQuery, Message


class Regexp(Filter):
    def __init__(self, regexp: str) -> NoReturn:
        self.regexp = re.compile(regexp)

    async def __call__(
        self,
        event: Message | CallbackQuery | InlineQuery,
    ) -> bool | dict[str, any]:
        if isinstance(event, Message):
            text = event.text
        elif isinstance(event, CallbackQuery):
            text = event.data
        elif isinstance(event, InlineQuery):
            text = event.query
        else:
            return False

        if not text:
            return False

        match = self.regexp.match(text)
        if match:
            return {
                'regexp': match,
            }
        return False
