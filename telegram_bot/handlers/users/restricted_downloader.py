from typing import NoReturn

from aiogram import Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from django.conf import settings
from django.utils.translation import gettext as _
from django_celery_beat.utils import now
from loguru import logger
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from telethon.utils import parse_phone

from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.filters.regexp import Regexp
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


# Start downloading
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
    await check_restricted_downloader_session(callback_query.message, state)

    await callback_query.message.answer(
        _('Please enter account phone number or session string'),
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
            await message.answer(_('Checking your session string'))

            client = CustomTelethonClient(session, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
            await client.connect()

            account = await check_client(client, message, state, user)
            if account:
                await message.delete()
                return
            return await message.answer(_('Invalid session string. Please enter valid session string'))

        if message.text.isnumeric():
            error_text = _('Invalid phone number format. Please enter phone number in international format')
        else:
            error_text = _('Invalid session string format. Please enter valid session string')
        return await message.answer(error_text)

    await message.answer(_('Please wait for a moment'))

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
        return await message.answer(_('Invalid code format. Please enter code you received in message'))

    await message.answer(_('Please wait for a moment'))

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
        await message.answer(_('Two-step verification is enabled. Please enter your password'))
        await state.set_state(RestrictedDownloaderForm.get_password)
        return
    except Exception as e:
        logger.exception(e)
        await message.answer(_('Failed to sign in. Please try again later or check your code'))
        return await client.sign_in(phone)

    await save_account_data(message, state, user, client)


@router.message(RestrictedDownloaderForm.get_password)
async def process_password(message: Message, state: FSMContext, user: User) -> NoReturn:
    """Process the password input from the user for two-factor authentication."""
    password = message.text
    await message.delete()

    await message.answer(_('Please wait for a moment'))

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
        await message.answer(_('Failed to sign in. Please try again later or check your password'))


async def save_account_data(
        message: Message,
        state: FSMContext,
        user: User,
        client: CustomTelethonClient,
) -> Account:
    telethon_user = await client.get_me()

    text = _('Account successfully added 🎉\n' '{id} {name} (@{username})').format(
        id=telethon_user.id, name=telethon_user.first_name + (telethon_user.last_name or ''),
        username=telethon_user.username
    )

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

    await state.clear()
    await state.set_state(RestrictedDownloaderForm.restricted_downloader_session)
    await message.answer(text)
    await start_restricted_downloader(message, state, user)

    return account
