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
        callback_data=f'restricted_downloader:add_account',
    )

    builder.adjust(1)

    return builder.as_markup()


def get_restricted_downloader_select_dialog_inline_markup() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_('📁 Select dialog'),
        switch_inline_query_current_chat=f'restricted_downloader:select_dialog:',
    )

    builder.adjust(1)

    return builder.as_markup()
