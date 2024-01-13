import csv

from aiogram import Router, Bot
from aiogram.filters import Command, or_f
from aiogram.types import Message, FSInputFile
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
        Command(commands=['export_users'])
    )
)
async def _export_users(message: Message):
    count = await User.objects.acount()

    file_path = settings.BASE_DIR / 'temp/users.csv'
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)

        writer.writerow(['id', 'name', 'username', 'language', 'created_at'])

        async for user in User.objects.all():
            writer.writerow([user.id, user.get_full_name(), user.username, user.language_code, user.date_joined])

    text_file = FSInputFile(path=file_path, filename='users.csv')
    await message.answer_document(text_file, caption=_('Total users: {count}').format(count=count))


@router.message(
    IsAdmin(),
    or_f(
        I18nText('Count users 👥'),
        Command(commands=['count_users'])
    )
)
async def _users_count(message: Message):
    count = await User.objects.acount()

    await message.answer(_('Total users: {count}').format(count=count))


@router.message(
    IsAdmin(),
    or_f(
        I18nText('Count active users 👥'),
        Command(commands=['count_active_users'])
    )
)
async def _active_users_count(message: Message, bot: Bot):
    count = 0
    async for user in User.objects.all():
        try:
            if await bot.send_chat_action(chat_id=user.telegram_id, action='typing'):
                count += 1
        except Exception as e:
            print(e)
            pass

    await message.answer(_('Active users: {count}').format(count=count))
