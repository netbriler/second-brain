import ipaddress
import struct
from typing import NoReturn
from uuid import uuid4

from aiogram import Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from django.conf import settings
from django.utils.translation import gettext as _
from loguru import logger
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from telethon.utils import parse_phone

from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.filters.regexp import Regexp
from telegram_bot.keyboards.inline.restricted_downloader import (
    get_restricted_downloader_select_account_inline_markup,
)
from telegram_bot.states.restricted_downloader import RestrictedDownloaderForm
from telegram_restricted_downloader.models import Account
from users.models import User

_STRUCT_PREFORMAT = '>B{}sH256s'

CURRENT_VERSION = '1'

router = Router(name=__name__)

clients = {}


async def check_learning_session(
    message: Message,
    state: FSMContext,
) -> FSMContext:
    if await state.get_state() != RestrictedDownloaderForm.restricted_downloader_session:
        await state.set_state(RestrictedDownloaderForm.restricted_downloader_session)

    return state


# Start downloading
@router.message(
    or_f(
        Command(commands=['restricted_downloader']),
        I18nText(_('Restricted downloader 📥')),
    ),
)
async def message_start_restricted_downloader(message: Message, state: FSMContext, user: User) -> NoReturn:
    await check_learning_session(message, state)

    accounts = [a async for a in Account.objects.filter(user=user).select_related('user')]
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
    user: User,
    state: FSMContext,
) -> NoReturn:
    await check_learning_session(callback_query, state)

    await callback_query.message.answer(
        _('Please enter account phone number'),
    )

    await state.set_state(RestrictedDownloaderForm.get_phone_number)


@router.message(RestrictedDownloaderForm.get_phone_number)
async def message_get_phone_number(message: Message, state: FSMContext) -> NoReturn:
    try:
        phone = parse_phone(message.text)
    except:
        return await message.answer(
            _('Invalid phone number format. Please enter phone number in international format'),
        )

    data = await state.get_data()
    if not data.get('session_file'):
        session_file = str(settings.BASE_DIR / f'temp/{str(uuid4()).replace("-", "")}')
        await state.update_data(session_file=session_file)
    else:
        session_file = data.get('session_file')

    if session_file not in clients:
        clients[session_file] = TelegramClient(
            session_file,
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH,
        )
    client = clients[session_file]

    await client.connect()
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


@router.message(RestrictedDownloaderForm.get_code)
async def message_get_code(message: Message, state: FSMContext, user: User) -> NoReturn:
    code = message.text
    if not code.isnumeric():
        return await message.answer(
            _('Invalid code format. Please enter code you received in message'),
        )

    data = await state.get_data()
    phone = data.get('phone')
    phone_code_hash = data.get('phone_code_hash')
    session_file = data.get('session_file')

    print(phone_code_hash, phone)

    if session_file not in clients:
        clients[session_file] = TelegramClient(
            session_file,
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH,
        )
        logger.info('Create new client')
    client = clients[session_file]
    await client.connect()
    try:
        self_user = await client.sign_in(
            code=code,
            phone=phone,
            phone_code_hash=phone_code_hash,
        )
    except SessionPasswordNeededError:
        await message.answer(
            _('Two step verification is enabled. Please enter your password'),
        )
        await state.set_state(RestrictedDownloaderForm.get_password)
        return
    except Exception as e:
        logger.exception(e)
        await client.sign_in(phone)
        phone, phone_code_hash = client._parse_phone_and_hash(None, None)
        await state.update_data(phone=phone, phone_code_hash=phone_code_hash)
        return await message.answer(
            _('Failed to sign in. Please try again later or check your code'),
        )

    text = _(
        'Account successfully added 🎉\n' '{id} {name} (@{username})',
    ).format(
        id=self_user.id,
        name=self_user.first_name + (self_user.last_name or ''),
        username=self_user.username,
    )

    ip = ipaddress.ip_address(client.session.server_address).packed
    session_string = CURRENT_VERSION + StringSession.encode(
        struct.pack(
            _STRUCT_PREFORMAT.format(len(ip)),
            client.session.dc_id,
            ip,
            client.session.port,
            client.session.auth_key.key,
        ),
    )

    await Account.objects.aupdate_or_create(
        user=user,
        phone=phone,
        name=f'{self_user.id} {self_user.first_name + (self_user.last_name or "")} (@{self_user.username})',
        encrypted_session_string=Account.encrypt(session_string),
    )

    await message.answer(text)

    await message_start_restricted_downloader(message, state, user)


@router.message(RestrictedDownloaderForm.get_password)
async def message_get_password(message: Message, state: FSMContext, user: User) -> NoReturn:
    password = message.text
    await message.delete()

    data = await state.get_data()
    phone = data.get('phone')
    session_file = data.get('session_file')

    if session_file not in clients:
        clients[session_file] = TelegramClient(
            session_file,
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH,
        )
        logger.info('Create new client')
    client = clients[session_file]
    await client.connect()
    try:
        self_user = await client.sign_in(password=password)
    except Exception as e:
        logger.exception(e)
        return await message.answer(
            _('Failed to sign in. Please try again later or check your password'),
        )

    text = _(
        'Account successfully added 🎉\n' '{id} {name} (@{username})',
    ).format(
        id=self_user.id,
        name=self_user.first_name + (self_user.last_name or ''),
        username=self_user.username,
    )

    ip = ipaddress.ip_address(client.session.server_address).packed
    session_string = CURRENT_VERSION + StringSession.encode(
        struct.pack(
            _STRUCT_PREFORMAT.format(len(ip)),
            client.session.dc_id,
            ip,
            client.session.port,
            client.session.auth_key.key,
        ),
    )

    await Account.objects.aupdate_or_create(
        user=user,
        phone=phone,
        name=f'{self_user.id} {self_user.first_name + (self_user.last_name or "")} (@{self_user.username})',
        encrypted_session_string=Account.encrypt(session_string),
    )

    await state.set_state(RestrictedDownloaderForm.restricted_downloader_session)

    await message.answer(text)

    await message_start_restricted_downloader(message, state, user)
