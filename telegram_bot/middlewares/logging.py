from collections.abc import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.enums import ReactionTypeType
from aiogram.types import Message, Update

from utils.logging import logger


class LoggingMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.counter = 0

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, any]], Awaitable[any]],
        event: Update,
        data: dict[str, any],
    ) -> any:
        if isinstance(event, Update):
            if event.message:
                if event.message.content_type == 'text':
                    logger.debug(
                        f'Received event [ID:{event.message.message_id}] from user [ID:{event.message.from_user.id}]\n'
                        f'in chat [ID:{event.message.chat.id}] text "{event.message.text}"',
                    )
                elif event.message.content_type == 'web_app_data':
                    logger.debug(
                        f'Received web app data [ID:{event.message.message_id}]\n'
                        f'from user [ID:{event.message.from_user.id}]\n'
                        f'in chat [ID:{event.message.chat.id}] data "{event.message.web_app_data}"',
                    )
            elif event.callback_query:
                logger.debug(
                    f'Received callback query [data:"{event.callback_query.data}"]\n'
                    f'from user [ID:{event.callback_query.from_user.id}]\n'
                    f'for event [ID:{event.callback_query.message.message_id}]\n'
                    f'in chat [ID:{event.callback_query.message.chat.id}]',
                )
            elif event.inline_query:
                logger.debug(
                    f'Received inline query [query:{event.inline_query.query}]\n'
                    f'from user [ID:{event.inline_query.from_user.id}]',
                )
            elif event.message_reaction:
                new_reactions = ''
                for reaction in event.message_reaction.new_reaction:
                    if reaction.type == ReactionTypeType.EMOJI:
                        new_reactions += f'{reaction.emoji} '
                    elif reaction.type == ReactionTypeType.CUSTOM_EMOJI:
                        new_reactions += 'unknown emoji '

                old_reactions = ''
                for reaction in event.message_reaction.old_reaction:
                    if reaction.type == ReactionTypeType.EMOJI:
                        old_reactions += f'{reaction.emoji} '
                    elif reaction.type == ReactionTypeType.CUSTOM_EMOJI:
                        old_reactions += 'unknown emoji '

                logger.debug(
                    f'Received message reaction [ID:{event.message_reaction.message_id}]\n'
                    f'from user [ID:{event.message_reaction.user.id}]\n'
                    f'in chat [ID:{event.message_reaction.chat.id}]\n'
                    f'old reaction: [{old_reactions}]\n'
                    f'new reaction: [{new_reactions}]',
                )

        return await handler(event, data)
