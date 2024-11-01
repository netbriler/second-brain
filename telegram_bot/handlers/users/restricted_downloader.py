import re
from typing import NoReturn

from aiogram import Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from django.conf import settings
from django.utils.translation import gettext as _
from django_celery_beat.utils import now
from loguru import logger
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from telethon.tl.types import MessageActionTopicCreate
from telethon.utils import parse_phone

from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.filters.regexp import Regexp
from telegram_bot.keyboards.default.cancel import get_cancel_markup
from telegram_bot.keyboards.default.default import get_default_markup
from telegram_bot.keyboards.inline.restricted_downloader import (
    get_restricted_downloader_select_account_inline_markup,
)
from telegram_bot.states.restricted_downloader import RestrictedDownloaderForm
from telegram_restricted_downloader.helpers import CustomTelethonClient
from telegram_restricted_downloader.models import Account
from users.models import User

router = Router(name=__name__)


async def check_restricted_downloader_session(
        message: Message,
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


@router.message(
    or_f(
        RestrictedDownloaderForm.restricted_downloader_session,
        RestrictedDownloaderForm.get_phone_number,
        RestrictedDownloaderForm.get_code,
        RestrictedDownloaderForm.get_password,
        RestrictedDownloaderForm.select_dialog,
    ),
    or_f(
        Command(commands=['cancel']),
        I18nText('Cancel ❌')
    ),
)
async def _cancel(message: Message, user: User, state: FSMContext) -> NoReturn:
    await state.clear()
    await message.answer(_('Choose an action from the menu 👇'), reply_markup=get_default_markup(user))


@router.message(
    or_f(
        Command(commands=['restricted_downloader']),
        I18nText(_('Restricted downloader 📥')),
    ),
)
async def start_restricted_downloader(message: Message, state: FSMContext, user: User) -> NoReturn:
    await check_restricted_downloader_session(message, state)

    accounts = [a async for a in Account.objects.filter(user=user, is_active=True).select_related('user')]
    await message.answer(
        _('Please select account to start downloading'),
        reply_markup=get_restricted_downloader_select_account_inline_markup(accounts),
    )


@router.callback_query(
    RestrictedDownloaderForm.restricted_downloader_session,
    Regexp(r'^restricted_downloader:add_account$'),
)
async def callback_add_account(
        callback_query: CallbackQuery,
        state: FSMContext,
) -> NoReturn:
    await callback_query.answer()

    await check_restricted_downloader_session(callback_query.message, state)

    await callback_query.message.answer(
        _('Please enter account phone number or session string'),
        reply_markup=get_cancel_markup()
    )

    await state.set_state(RestrictedDownloaderForm.get_phone_number)


@router.message(RestrictedDownloaderForm.get_phone_number)
async def message_get_phone_number(message: Message, state: FSMContext, user: User) -> NoReturn:
    session = None
    phone = None
    try:
        phone = parse_phone(message.text)
    except:
        pass

    if not phone:
        try:
            session = StringSession(message.text)
        except:
            pass

        if session is not None:
            await message.answer(
                _('Checking your session string'),
            )

            client = CustomTelethonClient(session, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
            await client.connect()

            account = await check_client(client, message, state, user)
            if account:
                await message.delete()
                return
            return await message.answer(
                _('Invalid session string. Please enter valid session string'),
                reply_markup=get_cancel_markup()
            )

        if message.text.isnumeric():
            error_text = _('Invalid phone number format. Please enter phone number in international format')
        else:
            error_text = _('Invalid session string format. Please enter valid session string')
        return await message.answer(
            error_text,
            reply_markup=get_cancel_markup()
        )

    await message.answer(
        _('Please wait for a moment'),
        reply_markup=get_cancel_markup()
    )

    data = await state.get_data()
    if not data.get('session_file'):
        session_file = str(settings.BASE_DIR / f'temp/{phone}')
        await state.update_data(session_file=session_file)
    else:
        session_file = data.get('session_file')

    client = CustomTelethonClient(session_file, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.connect()
    account = await check_client(client, message, state, user)
    if account:
        return

    try:
        await client.sign_in(phone)
        phone, phone_code_hash = client._parse_phone_and_hash(None, None)
    except Exception as e:
        logger.exception(e)
        return await message.answer(
            _('Failed to sign in. Please try again later or check your phone number'),
        )

    await state.update_data(phone=phone, phone_code_hash=phone_code_hash)

    await message.answer(
        _('Please enter code messaged to your phone number'),
    )

    await state.set_state(RestrictedDownloaderForm.get_code)

    await client.disconnect()


@router.message(RestrictedDownloaderForm.get_code)
async def process_verification_code(message: Message, state: FSMContext, user: User) -> NoReturn:
    code = message.text
    if not code.isnumeric():
        return await message.answer(
            _('Invalid code format. Please enter code you received in message'),
            reply_markup=get_cancel_markup()
        )

    await message.answer(
        _('Please wait for a moment'),
        reply_markup=get_cancel_markup()
    )

    data = await state.get_data()
    phone, phone_code_hash, session_file = data.get('phone'), data.get('phone_code_hash'), data.get('session_file')

    client = CustomTelethonClient(session_file, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.connect()
    account = await check_client(client, message, state, user)
    if account:
        return

    try:
        await client.sign_in(code=code, phone=phone, phone_code_hash=phone_code_hash)
    except SessionPasswordNeededError:
        await message.answer(
            _('Two-step verification is enabled. Please enter your password'),
        )
        await state.set_state(RestrictedDownloaderForm.get_password)
        return
    except Exception as e:
        logger.exception(e)
        await message.answer(
            _('Failed to sign in. Please try again later or check your code'),
        )
        return await client.sign_in(phone)

    await save_account_data(message, state, user, client)


@router.message(RestrictedDownloaderForm.get_password)
async def process_password(message: Message, state: FSMContext, user: User) -> NoReturn:
    """Process the password input from the user for two-factor authentication."""
    password = message.text
    await message.delete()

    await message.answer(
        _(
            'Please wait for a moment',
        ),
        reply_markup=get_cancel_markup()
    )

    data = await state.get_data()
    phone, session_file = data.get('phone'), data.get('session_file')

    client = CustomTelethonClient(session_file, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.connect()
    account = await check_client(client, message, state, user)
    if account:
        return

    try:
        await client.sign_in(password=password)
        await save_account_data(message, state, user, client)
    except Exception as e:
        logger.exception(e)
        await message.answer(
            _('Failed to sign in. Please try again later or check your password'),
        )


def get_account_text(account: Account) -> str:
    text = _(
        'Account Information\n\n'
        'ID: {id}\n'
        'Name: {name}\n'
        'Username: {username}\n'
        'Last used at: {last_used_at}\n'
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
        }
    )

    text = _('Account successfully added 🎉\n') + get_account_text(account)

    await state.clear()
    await state.set_state(RestrictedDownloaderForm.restricted_downloader_session)
    await message.answer(
        text,
        reply_markup=ReplyKeyboardRemove()
    )
    await start_restricted_downloader(message, state, user)

    return account


@router.callback_query(
    RestrictedDownloaderForm.restricted_downloader_session,
    Regexp(r'^restricted_downloader:select_account:(?P<account_id>\d+)$'),
)
async def callback_select_account(
        callback_query: CallbackQuery,
        state: FSMContext,
        regexp: re.Match,
        user: User,
) -> NoReturn:
    await callback_query.answer()

    account_id = int(regexp.group('account_id'))
    try:
        account = await Account.objects.aget(id=account_id, user=user, is_active=True)
    except Account.DoesNotExist:
        await callback_query.message.edit_reply_markup(
            reply_markup=get_restricted_downloader_select_account_inline_markup(
                [a async for a in Account.objects.filter(user=user, is_active=True).select_related('user')]
            ),
        )
        return await callback_query.answer(_('Account not found'), show_alert=True)

    await callback_query.message.answer(
        _('Selected account:\n') + get_account_text(account),
        reply_markup=get_cancel_markup(),
    )

    await callback_query.message.answer(
        _('Checking account session...'),
    )

    me = None
    try:
        if account.session_string:
            client = CustomTelethonClient(
                StringSession(account.session_string), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
            )
            await client.connect()
            me = await client.get_me()
    except Exception as e:
        logger.exception(e)

    if not me:
        return await callback_query.message.answer(
            _('Failed to check account session. Session is invalid. Please try again letter or re-add account'),
        )

    await callback_query.message.answer(
        _('Account session is valid. Select dialog or share link to download'),
    )

    await state.clear()
    await state.set_state(RestrictedDownloaderForm.select_dialog)
    await state.set_data({'account_id': account_id})


@router.message(
    RestrictedDownloaderForm.select_dialog,
    Regexp(
        r'^https:\/\/t\.me\/c\/'
        r'(?P<chat_id>\d+)'
        r'(\/(?P<chapter_id>\d+))?'
        r'(\/(?P<message_id>\d+))?$'
    ),
)
async def download_telegram_message(
        message: Message,
        regexp: re.Match,
        state: FSMContext,
        user: User,
) -> NoReturn:
    chat_id = int(regexp.group('chat_id')) if regexp.group('chat_id') else None
    chapter_id = int(regexp.group('chapter_id')) if regexp.group('chapter_id') else None
    message_id = int(regexp.group('message_id')) if regexp.group('message_id') else None
    if not message_id and chapter_id:
        message_id = chapter_id

    await message.answer(
        f'Chat ID: {chat_id}\n'
        f'Chapter ID: {chapter_id}\n'
        f'Message ID: {message_id}\n'
    )

    data = await state.get_data()
    account_id = data.get('account_id')
    try:
        account = await Account.objects.aget(id=account_id, user=user, is_active=True)
    except Account.DoesNotExist:
        await message.answer(_('Account not found'), show_alert=True)
        return await start_restricted_downloader(message, state, user)

    await message.answer(
        _('Please wait for a moment'),
        reply_markup=get_cancel_markup(),
    )

    me = None
    client = None
    try:
        if account.session_string:
            client = CustomTelethonClient(
                StringSession(account.session_string), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
            )
            await client.connect()
            me = await client.get_me()
    except Exception as e:
        logger.exception(e)

    if not me:
        await message.answer(
            _('Failed to check account session. Session is invalid. Please try again letter or re-add account'),
        )
        return await start_restricted_downloader(message, state, user)

    try:
        channel = await client.get_entity(int(f'-100{chat_id}'))
        text = _(
            'Detected Type: {type}\n'
            'ID: {id}\n'
            'Title: {title}\n'
        ).format(
            type=channel.__class__.__name__,
            id=channel.id,
            title=channel.title,
        )

        await message.answer(text)
    except Exception as e:
        logger.exception(e)
        return await message.answer(_('Failed to get channel information'))

    if message_id != chapter_id:
        try:
            _message = (await client.get_messages(channel, ids=[chapter_id]))[0]
            if isinstance(_message.action, MessageActionTopicCreate):
                text = _(
                    'Topic: {topic}\n'
                    'Created At: {created_at}\n'
                ).format(
                    topic=_message.action.title,
                    created_at=f'{_message.date:%Y-%m-%d %H:%M:%S}',
                )
            else:
                text = _(
                    'ID: {id}\n'
                    'Text: {text}\n'
                    'Document: {document}\n'
                ).format(
                    id=_message.id,
                    text=_message.text,
                    document=_message.document.mime_type if _message.document else '',
                )

            await message.answer(text)
        except Exception as e:
            logger.exception(e)
            return await message.answer(_('Failed to get message'))

    try:
        _message = (await client.get_messages(channel, ids=[message_id]))[0]
        if isinstance(_message.action, MessageActionTopicCreate):
            text = _(
                'Topic: {topic}\n'
                'Created At: {created_at}\n'
            ).format(
                topic=_message.action.title,
                created_at=f'{_message.date:%Y-%m-%d %H:%M:%S}',
            )
        else:
            text = _(
                'ID: {id}\n'
                'Text: {text}\n'
                'Document: {document}\n'
            ).format(
                id=_message.id,
                text=_message.text,
                document=_message.document.mime_type if _message.document else '',
            )

        await message.answer(text)
    except Exception as e:
        logger.exception(e)
        return await message.answer(_('Failed to get message'))
