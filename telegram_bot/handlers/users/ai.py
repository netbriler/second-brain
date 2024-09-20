import re
from typing import NoReturn

from aiogram import Router
from aiogram.types import CallbackQuery, ReactionTypeEmoji
from django.utils.translation import gettext as _

from ai.models import Message as AiMessage
from ai.services.base import ReminderRecognition, TextRecognition
from ai.tasks import process_category_massage
from reminders.reminders_tasks.telegram_reminder import TelegramReminderTask
from reminders.services import create_reminder
from telegram_bot.filters.regexp import Regexp
from users.models import User

router = Router(name=__name__)


@router.callback_query(
    Regexp(r'^ai_task:category_(\w+)_(\d+)$'),
)
async def _category(callback_query: CallbackQuery, regexp: re.Match) -> NoReturn:
    category = regexp.group(1)
    ai_message_id = regexp.group(2)
    try:
        ai_message = await AiMessage.objects.aget(id=ai_message_id)
    except AiMessage.DoesNotExist:
        return await callback_query.answer(_('Message not found'))

    try:
        text = TextRecognition.model_validate_json(ai_message.response).text
    except Exception as e:  # noqa
        return await callback_query.answer(str(e)[:1200])

    await callback_query.message.answer(_('Category: {category}\n\n{text}').format(category=category, text=text))

    if not process_category_massage(ai_message_id, category):
        return await callback_query.answer(_('Unknown category'))

    await callback_query.bot.send_chat_action(callback_query.message.chat.id, 'typing')
    await callback_query.answer(_('Parsing message...'))
    await callback_query.message.react([ReactionTypeEmoji(emoji='👀')])
    await callback_query.message.edit_reply_markup()


@router.callback_query(
    Regexp(r'^ai_task:reminder_create_(\d+)$'),
)
async def _reminder_save(callback_query: CallbackQuery, regexp: re.Match, user: User) -> NoReturn:
    ai_message_id = regexp.group(1)
    try:
        ai_message = await AiMessage.objects.aget(id=ai_message_id)
    except AiMessage.DoesNotExist:
        return await callback_query.answer(_('Message not found'))

    try:
        reminder = ReminderRecognition.model_validate_json(ai_message.response)
    except Exception as e:  # noqa
        return await callback_query.answer(str(e)[:1200])

    reminder = await create_reminder(
        user=user,
        title=reminder.title,
        crontab_string=reminder.crontab_string,
        description=reminder.description,
        task_class=TelegramReminderTask,
        data={
            'text': reminder.message,
        },
    )

    await callback_query.message.answer(_('Reminder saved successfully'))
    await callback_query.message.edit_reply_markup()
