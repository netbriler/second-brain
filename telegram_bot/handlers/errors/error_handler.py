import contextlib
import traceback
from typing import NoReturn

from aiogram import Router
from aiogram.types import ErrorEvent
from django.utils.translation import gettext as _

from utils.logging import logger

router = Router(name=__name__)


@router.error()
async def error_handler(event: ErrorEvent) -> NoReturn:
    try:
        raise event.exception
    except:  # noqa
        exception_traceback = traceback.format_exc()

    logger.exception(f'Update: {event.update} \n{exception_traceback}')

    if event.update.message:
        with contextlib.suppress(Exception):
            await event.update.message.answer(_('Something went wrong.'))
    elif event.update.callback_query:
        with contextlib.suppress(Exception):
            await event.update.callback_query.answer(_('Something went wrong.'))
