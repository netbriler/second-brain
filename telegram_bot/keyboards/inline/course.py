from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.utils.translation import gettext as _
from pyrogram.types import InlineKeyboardMarkup

from courses.models import Course, Group, Lesson


def get_course_inline_markup(course: Course) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_('📚 {title}').format(title=course.title),
        switch_inline_query_current_chat=f'course_{course.id}',
    )

    builder.adjust(1)

    return builder.as_markup()


def get_group_inline_markup(group: Group) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if group.course:
        builder.button(
            text=_('📚 {course_title}').format(course_title=group.course.title),
            switch_inline_query_current_chat=f'course_{group.course.id}',
        )

    if group.parent:
        builder.button(
            text=_('📁 {group_title}').format(group_title=group.parent.title),
            switch_inline_query_current_chat=f'group_{group.parent.id}',
        )

    builder.button(
        text=_('📁 {title}').format(title=group.title),
        switch_inline_query_current_chat=f'group_{group.id}',
    )

    builder.adjust(1)

    return builder.as_markup()


def get_lesson_inline_markup(lesson: Lesson) -> InlineKeyboardMarkup | None:
    if not lesson.course and not lesson.group:
        return None
    builder = InlineKeyboardBuilder()

    if lesson.course:
        builder.button(
            text=_('📚 {course_title}').format(course_title=lesson.course.title),
            switch_inline_query_current_chat=f'course_{lesson.course.id}',
        )

    if lesson.group:
        builder.button(
            text=_('📁 {group_title}').format(group_title=lesson.group.title),
            switch_inline_query_current_chat=f'group_{lesson.group.id}',
        )

    builder.adjust(1)

    return builder.as_markup()
