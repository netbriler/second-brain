from typing import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.types import Message, CallbackQuery, InlineQuery
from aiogram.utils.chat_action import ChatActionSender
from django.utils.translation import override

from users.services import get_or_create_user


class UsersMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, dict[str, any]], Awaitable[any]],
            event: Message | CallbackQuery | InlineQuery,
            data: dict[str, any]
    ) -> any:
        user = None
        if hasattr(event, 'from_user'):
            user = event.from_user
        elif 'event_from_user' in data:
            user = data['event_from_user']

        if not user:
            raise CancelHandler()

        async with ChatActionSender.typing(bot=data['bot'], chat_id=user.id):
            data['user'] = await get_or_create_user(
                telegram_id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                telegram_username=user.username,
                language_code=user.language_code
            )
            with override(data['user'].language_code):
                return await handler(event, data)
