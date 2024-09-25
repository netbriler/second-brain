from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.utils.translation import gettext as _


def get_help_inline_markup():
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_('🔍 Search Courses'),
        switch_inline_query_current_chat='',
    )
    builder.button(
        text=_('📚 Course by ID'),
        switch_inline_query_current_chat='course_',
    )
    builder.button(
        text=_('📁 Group by ID'),
        switch_inline_query_current_chat='group_',
    )
    builder.button(
        text=_('📝 Lesson by ID'),
        switch_inline_query_current_chat='lesson_',
    )

    builder.adjust(1, 3)

    return builder.as_markup()
