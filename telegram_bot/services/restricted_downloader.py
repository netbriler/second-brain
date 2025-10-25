from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from django.utils.translation import gettext as _
from django_celery_beat.utils import now
from loguru import logger
from telethon._updates import Entity
from telethon.tl.types import MessageActionTopicCreate

from telegram_bot.states.restricted_downloader import RestrictedDownloaderForm
from telegram_restricted_downloader.helpers import CustomTelethonClient
from telegram_restricted_downloader.models import Account
from users.models import User


def get_account_text(account: Account) -> str:
    text = _(
        'Account Information\n\n'
        'ID: {id}\n'
        'Name: {name}\n'
        'Username: {username}\n'
        'Last used at: {last_used_at}\n',
    ).format(
        id=account.telegram_id,
        name=account.name,
        username='@' + account.username if account.username else '',
        last_used_at=f'{account.last_used_at:%Y-%m-%d %H:%M:%S}' if account.last_used_at else '',
    )

    return text


async def save_account_data(
        message: Message,
        state: FSMContext,
        user: User,
        client: CustomTelethonClient,
) -> Account:
    telethon_user = await client.get_me()

    session_string = client.get_session_string()
    account, created = await Account.objects.aupdate_or_create(
        telegram_id=telethon_user.id,
        user=user,
        defaults={
            'phone': telethon_user.phone,
            'name': f'{telethon_user.first_name + (telethon_user.last_name or "")}',
            'username': telethon_user.username,
            'encrypted_session_string': Account.encrypt(session_string),
            'last_used_at': now(),
        },
    )

    text = _('Account successfully added 🎉\n') + get_account_text(account)

    await state.clear()
    await state.set_state(RestrictedDownloaderForm.restricted_downloader_session)
    await message.answer(
        text,
        reply_markup=ReplyKeyboardRemove(),
    )

    return account


async def check_restricted_downloader_session(
        state: FSMContext,
) -> FSMContext:
    if await state.get_state() != RestrictedDownloaderForm.restricted_downloader_session:
        await state.set_state(RestrictedDownloaderForm.restricted_downloader_session)

    return state


async def check_client(client: CustomTelethonClient, message: Message, state: FSMContext, user: User) -> Account:
    if await client.is_user_authorized():
        return await save_account_data(
            message,
            state,
            user=user,
            client=client,
        )


# Helper Functions
def get_channel_text(channel):
    """Format channel information."""
    return _('Detected Type: {type}\nID: {id}\nTitle: {title}\n').format(
        type=channel.__class__.__name__,
        id=channel.id,
        title=channel.title,
    )


def get_topic_text(_message):
    """Format topic creation message information."""
    return _(
        'ID: {id}\nTopic: {topic}\nCreated At: {created_at}\n',
    ).format(
        id=_message.id,
        topic=(_message.action.title[:100] + '...' if len(
            _message.action.title,
        ) > 100 else '') if _message.action.title else '',
        created_at=f'{_message.date:%Y-%m-%d %H:%M:%S}',
    )


def get_message_text(_message):
    """Format general message information."""
    return _(
        'ID: {id}\nDocument: {document}\nText: {text}\n',
    ).format(
        id=_message.id,
        text=(_message.text[:100] + '...' if len(_message.text) > 100 else '') if _message.text else '',
        document=_message.document.mime_type if _message.document else '',
    )


# Main Functions
async def fetch_channel_info(client, chat_id) -> tuple[Entity | None, str]:
    try:
        channel = await client.get_entity(
            int(f'-100{chat_id}' if not str(chat_id).startswith('-100') else chat_id),
        )
        return channel, get_channel_text(channel)
    except Exception as e:
        logger.exception(e)
        return None, _('Failed to get channel information')


async def fetch_message_details(client, channel, message_id) -> tuple[Entity | None, str]:
    try:
        _message = (await client.get_messages(channel, ids=[message_id]))[0]
        if isinstance(_message.action, MessageActionTopicCreate):
            return _message, get_topic_text(_message)
        else:
            return _message, get_message_text(_message)
    except Exception as e:
        logger.exception(e)
        return None, _('Failed to get message')
