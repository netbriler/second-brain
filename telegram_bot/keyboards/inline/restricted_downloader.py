from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.utils.translation import gettext as _

from telegram_restricted_downloader.models import Account


def get_restricted_downloader_select_account_inline_markup(accounts: list[Account]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for account in accounts:
        builder.button(
            text=f'{account.telegram_id} {account.name}',
            callback_data=f'restricted_downloader:select_account:{account.id}',
        )

    builder.button(
        text=_('Add new account 🆕'),
        callback_data='restricted_downloader:add_account',
    )

    builder.adjust(1)

    return builder.as_markup()


def get_restricted_downloader_select_dialog_inline_markup(channel_selected: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if channel_selected:
        builder.button(
            text=_('📁 Select chapter'),
            switch_inline_query_current_chat='restricted_downloader:select_dialog:',
        )
        builder.button(
            text=_('✏️ Change sender account'),
            switch_inline_query_current_chat='restricted_downloader:select_sender_account',
        )
        builder.button(
            text=_('✏️ Change receiver account'),
            switch_inline_query_current_chat='restricted_downloader:select_receiver_account',
        )
        builder.button(
            text=_('🚀 Start downloading'),
            switch_inline_query_current_chat='restricted_downloader:start_downloading',
        )
    else:
        builder.button(
            text=_('📁 Select dialog'),
            switch_inline_query_current_chat='restricted_downloader:select_dialog:',
        )

    builder.adjust(1)

    return builder.as_markup()
