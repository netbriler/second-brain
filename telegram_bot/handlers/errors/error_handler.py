import contextlib
import traceback
from typing import NoReturn

from aiogram import Router
from aiogram.types import ErrorEvent
from django.conf import settings
from django.utils.translation import gettext as _

from users.models import User
from utils.logging import logger

router = Router(name=__name__)


@router.error()
async def error_handler(event: ErrorEvent, user: User = None) -> NoReturn:
    try:
        raise event.exception
    except:  # noqa
        exception_traceback = traceback.format_exc()

    logger.exception(f'Update: {event.update} \n{exception_traceback}')

    if not user:
        try:
            if event.update.message:
                user = await User.objects.aget(telegram_id=event.update.message.from_user.id)
            elif event.update.callback_query:
                user = await User.objects.aget(telegram_id=event.update.callback_query.from_user.id)
        except Exception:
            pass

    error_message = _('Something went wrong.')
    if user and user.is_superuser and settings.DEBUG:
        error_message = f'<b>Error occurred:</b>\n\n<code>{exception_traceback[4000:]
        if len(exception_traceback) > 4000 else exception_traceback}</code>'

    if event.update.message:
        with contextlib.suppress(Exception):
            await event.update.message.answer(error_message)
    elif event.update.callback_query:
        with contextlib.suppress(Exception):
            await event.update.callback_query.answer(error_message)
