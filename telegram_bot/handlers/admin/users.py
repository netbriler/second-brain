import contextlib
import csv
import re
from pathlib import Path
from typing import NoReturn

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject, or_f
from aiogram.types import FSInputFile, Message
from django.conf import settings
from django.utils.translation import gettext as _

from telegram_bot.filters.admin import IsAdmin
from telegram_bot.filters.i18n_text import I18nText
from users.models import User

router = Router(name=__name__)


@router.message(
    IsAdmin(),
    or_f(
        I18nText('Export users 📁'),
        Command(commands=['export_users']),
    ),
)
async def _export_users(message: Message) -> NoReturn:
    count = await User.objects.acount()

    file_path = settings.BASE_DIR / 'temp/users.csv'
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with Path.open(file_path, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)

        writer.writerow(
            [
                'id',
                'name',
                'username',
                'language',
                'telegram_is_active',
                'telegram_activity_at',
                'date_joined',
            ],
        )

        async for user in User.objects.all():
            writer.writerow(
                [
                    user.id,
                    user.full_name,
                    user.username,
                    user.language_code,
                    user.telegram_is_active,
                    user.telegram_activity_at,
                    user.date_joined,
                ],
            )

    text_file = FSInputFile(path=file_path, filename='users.csv')
    await message.answer_document(text_file, caption=_('Total users: {count}').format(count=count))


@router.message(
    IsAdmin(),
    or_f(
        I18nText('Count users 👥'),
        Command(commands=['count_users']),
    ),
)
async def _users_count(message: Message) -> NoReturn:
    count = await User.objects.acount()

    await message.answer(_('Total users: {count}').format(count=count))


@router.message(
    IsAdmin(),
    or_f(
        I18nText('Count active users 👥'),
        Command(commands=['count_active_users']),
    ),
)
async def _active_users_count(message: Message, bot: Bot) -> NoReturn:
    count = 0
    async for user in User.objects.all():
        with contextlib.suppress(Exception):
            if await bot.send_chat_action(chat_id=user.telegram_id, action='typing'):
                count += 1

    await message.answer(_('Active users: {count}').format(count=count))


@router.message(
    IsAdmin(),
    Command(re.compile(r'user[\s|_]?@?([\d|\w]*)', re.IGNORECASE)),
)
async def _user(message: Message, bot: Bot, command: CommandObject) -> NoReturn:
    search_user = command.regexp_match.group(1) or command.args
    search_user = search_user.strip().lower().replace('@', '')
    if not search_user:
        return await message.answer(_('Usage:\n/user [user_id | username]'))

    if search_user.isnumeric():
        found_user: User = await User.objects.filter(telegram_id=int(search_user)).afirst()
    else:
        found_user: User = await User.objects.filter(telegram_username__iexact=search_user).afirst()

    if not found_user:
        await message.answer(_('User not found'))
        return NoReturn

    text = _(
        'User info:\n'
        '<b>ID</b>: <a href="tg://user?id={id}">{id}</a>\n'
        '<b>Name</b>: {name}\n'
        '<b>Username</b>: @{username}\n'
        '<b>Language</b>: {language}\n'
        '<b>Is admin</b>: {is_admin}\n'
        '<b>Is active</b>: {is_active}\n'
        '<b>Telegram is active</b>: {telegram_is_active}\n'
        '<b>Last activity at</b>: {telegram_activity_at}\n'
        '<b>Joined at</b>: {date_joined}\n',
    ).format(
        id=found_user.telegram_id,
        name=found_user.full_name,
        username=found_user.telegram_username,
        language=f'{found_user.get_language_code_display()} ({found_user.language_code})',
        is_admin='✅' if found_user.is_superuser else '❌',
        is_active='✅' if found_user.is_active else '❌',
        telegram_is_active='✅' if found_user.telegram_is_active else '❌',
        telegram_activity_at=found_user.telegram_activity_at.strftime(settings.DATETIME_FORMAT),
        date_joined=found_user.date_joined.strftime(settings.DATETIME_FORMAT),
    )

    photo = await bot.get_user_profile_photos(found_user.telegram_id, limit=1)
    if photo.photos:
        await message.answer_photo(photo.photos[0][-1].file_id, caption=text)
    else:
        await message.answer(text)
