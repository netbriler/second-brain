from contextlib import suppress

from aiogram import Bot
from aiogram.fsm.context import FSMContext


async def clean_messages(
    bot: Bot,
    state: FSMContext,
    chat_id: int,
    key: str = 'messages_to_clean',
):
    data = await state.get_data()
    messages_to_clean = data.get(key, [])

    for message_id in messages_to_clean:
        with suppress(Exception):
            await bot.delete_message(
                chat_id=chat_id,
                message_id=message_id,
            )

    data = await state.get_data()
    new_messages_to_clean = [message_id for message_id in data.get(key, []) if message_id not in messages_to_clean]
    await state.update_data({key: new_messages_to_clean})


async def add_message_to_clean(state: FSMContext, message_id: int, key: str = 'messages_to_clean'):
    data = await state.get_data()
    messages = data.get(key, [])
    messages.append(message_id)
    await state.update_data({key: messages})
