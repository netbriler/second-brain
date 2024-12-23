import re
from typing import NoReturn

from aiogram import Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineQueryResultArticle, InputTextMessageContent
from django.conf import settings
from django.utils.translation import gettext as _
from loguru import logger
from telethon import functions
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from telethon.utils import parse_phone

from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.filters.regexp import Regexp
from telegram_bot.keyboards.default.cancel import get_cancel_markup
from telegram_bot.keyboards.default.default import get_default_markup
from telegram_bot.keyboards.inline.restricted_downloader import (
    get_restricted_downloader_select_account_inline_markup, get_restricted_downloader_select_dialog_inline_markup,
)
from telegram_bot.services.restricted_downloader import get_account_text, save_account_data, \
    check_restricted_downloader_session, check_client, fetch_channel_info, fetch_message_details
from telegram_bot.states.restricted_downloader import RestrictedDownloaderForm
from telegram_restricted_downloader.helpers import CustomTelethonClient
from telegram_restricted_downloader.models import Account
from users.models import User

router = Router(name=__name__)


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
    await check_restricted_downloader_session(state)

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

    await check_restricted_downloader_session(state)

    await callback_query.message.answer(
        _('Please enter account phone number or session string'),
        reply_markup=get_cancel_markup(_('Phone number or session string:'))
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
                return await start_restricted_downloader(message, state, user)
            return await message.answer(
                _('Invalid session string. Please enter valid session string'),
            )

        if message.text.isnumeric():
            error_text = _('Invalid phone number format. Please enter phone number in international format')
        else:
            error_text = _('Invalid session string format. Please enter valid session string')
        return await message.answer(
            error_text,
        )

    await message.answer(
        _('Please wait for a moment'),
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
        return await start_restricted_downloader(message, state, user)

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
        reply_markup=get_cancel_markup(_('Code:'))
    )

    await state.set_state(RestrictedDownloaderForm.get_code)

    await client.disconnect()


@router.message(RestrictedDownloaderForm.get_code)
async def process_verification_code(message: Message, state: FSMContext, user: User) -> NoReturn:
    code = message.text
    if not code.isnumeric():
        return await message.answer(
            _('Invalid code format. Please enter code you received in message'),
        )

    await message.answer(
        _('Please wait for a moment'),
    )

    data = await state.get_data()
    phone, phone_code_hash, session_file = data.get('phone'), data.get('phone_code_hash'), data.get('session_file')

    client = CustomTelethonClient(session_file, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.connect()
    account = await check_client(client, message, state, user)
    if account:
        return await start_restricted_downloader(message, state, user)

    try:
        await client.sign_in(code=code, phone=phone, phone_code_hash=phone_code_hash)
    except SessionPasswordNeededError:
        await message.answer(
            _('Two-step verification is enabled. Please enter your password, it will be deleted instantly'),
            reply_markup=get_cancel_markup(_('Password:'))
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
    await start_restricted_downloader(message, state, user)


@router.message(RestrictedDownloaderForm.get_password)
async def process_password(message: Message, state: FSMContext, user: User) -> NoReturn:
    """Process the password input from the user for two-factor authentication."""
    password = message.text
    await message.delete()

    await message.answer(
        _(
            'Please wait for a moment',
        ),
    )

    data = await state.get_data()
    phone, session_file = data.get('phone'), data.get('session_file')

    client = CustomTelethonClient(session_file, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.connect()
    account = await check_client(client, message, state, user)
    if account:
        return await start_restricted_downloader(message, state, user)

    try:
        await client.sign_in(password=password)
        await save_account_data(message, state, user, client)
        await start_restricted_downloader(message, state, user)
    except Exception as e:
        logger.exception(e)
        await message.answer(
            _('Failed to sign in. Please try again later or check your password'),
        )


@router.callback_query(
    or_f(
        RestrictedDownloaderForm.restricted_downloader_session,
        RestrictedDownloaderForm.select_dialog,
    ),
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
        reply_markup=get_restricted_downloader_select_dialog_inline_markup(),
    )

    await state.clear()
    await state.set_state(RestrictedDownloaderForm.select_dialog)
    await state.set_data({'account_id': account_id})


@router.message(
    RestrictedDownloaderForm.select_dialog,
    Regexp(
        r'^https:\/\/t\.me\/c\/'
        r'(?P<chat_id>-?\d+)'
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
    chat_id = int(str(regexp.group('chat_id') or 0).replace('-100', ''))
    chapter_id = int(regexp.group('chapter_id') or 0)
    message_id = int(regexp.group('message_id') or chapter_id)

    await message.answer(
        f'Chat ID: {chat_id}\nChapter ID: {chapter_id}\nMessage ID: {message_id}\n'
    )

    data = await state.get_data()
    account_id = data.get('account_id')
    channel_id = data.get('channel_id')
    sender_account_id = data.get('sender_account_id')
    receiver_chat_id = data.get('receiver_chat_id', user.telegram_id)
    if channel_id and chat_id != channel_id:
        return await message.answer(
            _(f'You can download messages only from one channel. t.me/c/{channel_id}'), show_alert=True
        )

    try:
        account = await Account.objects.aget(id=account_id, user=user, is_active=True)
    except Account.DoesNotExist:
        await message.answer(_('Account not found'), show_alert=True)
        return await start_restricted_downloader(message, state, user)

    sender_account = None
    if sender_account_id:
        try:
            sender_account = await Account.objects.aget(id=sender_account_id, user=user, is_active=True)
        except Account.DoesNotExist:
            await message.answer(_('Sender account not found'), show_alert=True)
            return await start_restricted_downloader(message, state, user)

    await message.answer(_('Please wait for a moment'), reply_markup=get_cancel_markup())

    client, me = None, None
    try:
        if account.session_string:
            client = CustomTelethonClient(
                StringSession(account.session_string),
                settings.TELEGRAM_API_ID,
                settings.TELEGRAM_API_HASH,
            )
            await client.connect()
            me = await client.get_me()
    except Exception as e:
        logger.exception(e)

    if not me:
        await message.answer(
            _('Failed to check account session. Session is invalid. Please try again later or re-add account'),
        )
        return await start_restricted_downloader(message, state, user)

    channel, text = await fetch_channel_info(client, chat_id)
    await message.answer(text)
    if not channel:
        return

    if chapter_id and message_id != chapter_id:
        chapter, text = await fetch_message_details(client, channel, chapter_id)
        await message.answer(text)

    if message_id:
        _message, text = await fetch_message_details(client, channel, message_id)
        await message.answer(text)

    if 'chapter_ids' not in data:
        data['chapter_ids'] = []
    if 'message_ids' not in data:
        data['message_ids'] = []
    if chapter_id:
        data['chapter_ids'].append(chapter_id)
    if message_id and message_id != chapter_id:
        data['message_ids'].append(message_id)

    await state.update_data(
        chapter_ids=list(set(data['chapter_ids'])),
        message_ids=list(set(data['message_ids'])),
        channel_id=chat_id,
        receiver_chat_id=receiver_chat_id,
    )

    data = await state.get_data()

    if sender_account:
        sender_account_text = f'{sender_account.telegram_id} {sender_account.name}'
    else:
        bot = await message.bot.get_me()
        sender_account_text = f'{bot.id} {bot.full_name}'

    await message.answer(
        _(
            'Message to fetch:\n'
            'Channel ID: {channel_id}\n'
            'Chapter IDs: {chapter_ids}\n'
            'Message IDs: {message_ids}\n\n'
            'From account:\n{account_text}\n'
            'Sender:\n{sender_text}\n'
            'Receiver chat id: {receiver_chat_id}'
            '\n\n'
            'Add more messages or start downloading?',
        ).format(
            channel_id=data.get('channel_id'),
            chapter_ids=data.get('chapter_ids'),
            message_ids=data.get('message_ids'),
            account_text=f'{account.telegram_id} {account.name}',
            sender_text=sender_account_text,
            receiver_chat_id=receiver_chat_id,
        ),
        reply_markup=get_restricted_downloader_select_dialog_inline_markup(True),
    )


# restricted_downloader:start_downloading
@router.callback_query(
    RestrictedDownloaderForm.select_dialog,
    Regexp(r'^restricted_downloader:start_downloading$'),
)
async def start_downloading(callback_query: CallbackQuery, state: FSMContext) -> NoReturn:
    await callback_query.answer()

    data = await state.get_data()
    account_id = data.get('account_id')
    channel_id = data.get('channel_id')
    chapter_ids = data.get('chapter_ids')
    message_ids = data.get('message_ids')

    try:
        account = await Account.objects.aget(id=account_id)
    except Account.DoesNotExist:
        return await callback_query.message.answer(_('Account not found'), show_alert=True)

    await callback_query.message.answer(
        _('Please wait for a moment'),
    )

    client, me = None, None
    try:
        if account.session_string:
            client = CustomTelethonClient(
                StringSession(account.session_string),
                settings.TELEGRAM_API_ID,
                settings.TELEGRAM_API_HASH,
            )
            await client.connect()
            me = await client.get_me()
    except Exception as e:
        logger.exception(e)

    if not me:
        return await callback_query.message.answer(
            _('Failed to check account session. Session is invalid'),
        )


@router.inline_query(
    RestrictedDownloaderForm.select_dialog,
    Regexp(r'^restricted_downloader:select_dialog:(?P<search>.*)$'),
)
async def inline_select_dialog(
        query: CallbackQuery,
        state: FSMContext,
        user: User,
        regexp: re.Match
) -> NoReturn:
    search_query = (regexp.group('search') or '').strip().lower()

    data = await state.get_data()
    account_id = data.get('account_id')
    channel_id = data.get('channel_id')

    results = []
    try:
        account = await Account.objects.aget(id=account_id, user=user, is_active=True)
    except Account.DoesNotExist:
        results.append(
            InlineQueryResultArticle(
                id='account_not_found',
                title=_('Account not found'),
                description=_('Please select account again'),
                input_message_content=InputTextMessageContent(
                    message_text=f'/restricted_downloader',
                ),
            ),
        )

        return await query.answer(
            results=results,
            cache_time=0,
        )

    client, me = None, None
    try:
        if account.session_string:
            client = CustomTelethonClient(
                StringSession(account.session_string),
                settings.TELEGRAM_API_ID,
                settings.TELEGRAM_API_HASH,
            )
            await client.connect()
            me = await client.get_me()
    except Exception as e:
        logger.exception(e)

    if not me:
        results.append(
            InlineQueryResultArticle(
                id='invalid_session',
                title=_('Invalid session'),
                description=_('Please re-add account'),
                input_message_content=InputTextMessageContent(
                    message_text=f'/restricted_downloader',
                ),
            ),
        )

        return await query.answer(
            results=results,
            cache_time=0,
        )
    if channel_id:
        channel, __ = await fetch_channel_info(client, channel_id)

        result = await client(
            functions.channels.GetForumTopicsRequest(
                channel=channel,
                offset_date=None,
                offset_id=0,
                offset_topic=0,
                limit=100,
                q=search_query,
            )
        )
        for topic in result.topics:
            results.append(
                InlineQueryResultArticle(
                    id=str(topic.id),
                    title=f'{topic.id}: {topic.title}',
                    input_message_content=InputTextMessageContent(
                        message_text=f'https://t.me/c/{channel_id}/{topic.id}',
                    ),
                ),
            )
    else:
        async for dialog in client.iter_dialogs(limit=50):
            if not hasattr(dialog.entity, 'noforwards') or not dialog.entity.noforwards:
                continue

            if search_query and search_query not in dialog.title.lower():
                continue

            results.append(
                InlineQueryResultArticle(
                    id=str(dialog.id),
                    title=f'{dialog.entity.__class__.__name__}: {dialog.title}',
                    input_message_content=InputTextMessageContent(
                        message_text=f'https://t.me/c/{str(dialog.id).replace("-100", "")}',
                    ),
                ),
            )

    return await query.answer(
        results=results,
        cache_time=0,
    )
