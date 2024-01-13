from typing import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineQuery

from utils.logging import logger


class LoggingMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.counter = 0

    async def __call__(
            self,
            handler: Callable[[Message, dict[str, any]], Awaitable[any]],
            event: Message | CallbackQuery | InlineQuery,
            data: dict[str, any]
    ) -> any:
        print(f'{handler=}')
        print(f'{event=}')

        if isinstance(event, Message):
            if event.content_type == 'text':
                logger.debug(
                    f'Received event [ID:{event.message_id}] from user [ID:{event.from_user.id}] '
                    f'in chat [ID:{event.chat.id}] text "{event.text}"'
                )
            elif event.content_type == 'web_app_data':
                logger.debug(
                    f'Received web app data [ID:{event.message_id}] from user [ID:{event.from_user.id}] '
                    f'in chat [ID:{event.chat.id}] data "{event.web_app_data}"'
                )
        elif isinstance(event, CallbackQuery):
            logger.debug(
                f'Received callback query [data:"{event.data}"] '
                f'from user [ID:{event.from_user.id}] '
                f'for event [ID:{event.event.message_id}] '
                f'in chat [ID:{event.event.chat.id}]'
            )
        elif isinstance(event, InlineQuery):
            logger.debug(
                f'Received inline query [query:{event.query}] from user [ID:{event.from_user.id}]'
            )

        return await handler(event, data)
