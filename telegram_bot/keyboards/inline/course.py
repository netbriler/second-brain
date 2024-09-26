from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.utils.translation import gettext as _
from pyrogram.types import InlineKeyboardMarkup

from courses.models import Course, Group, Lesson


def get_course_inline_markup(course: Course) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_('📁 Groups & Lessons'),
        switch_inline_query_current_chat=f'courses:course_{course.id}',
    )
    # all courses
    builder.button(
        text=_('🔍 Search Courses'),
        switch_inline_query_current_chat='courses:',
    )
    builder.button(
        text=_('📊 Statistics'),
        callback_data=f'courses:course_{course.id}:stats',
    )

    builder.adjust(1)

    return builder.as_markup()


def get_group_inline_markup(group: Group) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_('📝 Lessons'),
        switch_inline_query_current_chat=f'courses:group_{group.id}',
    )

    if group.parent:
        builder.button(
            text=_('📁 {group_title}').format(group_title=group.parent.title),
            switch_inline_query_current_chat=f'courses:group_{group.parent.id}',
        )

    if group.course:
        builder.button(
            text=_('📚 {course_title}').format(course_title=group.course.title),
            switch_inline_query_current_chat=f'courses:course_{group.course.id}',
        )

    builder.button(
        text=_('📊 Statistics'),
        callback_data=f'courses:group_{group.id}:stats',
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
            switch_inline_query_current_chat=f'courses:course_{lesson.course.id}',
        )

    if lesson.group:
        builder.button(
            text=_('📁 {group_title}').format(group_title=lesson.group.title),
            switch_inline_query_current_chat=f'courses:group_{lesson.group.id}',
        )

    builder.adjust(1)

    return builder.as_markup()


def get_start_learning_inline_markup(lesson: Lesson) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if lesson:
        builder.button(
            text=_('📚 Continue learning'),
            callback_data=f'courses:lesson_{lesson.id}',
        )
        builder.button(
            text=_('🔍 Search Courses'),
            switch_inline_query_current_chat='courses:',
        )
    else:
        builder.button(
            text=_('📚 Start learning'),
            switch_inline_query_current_chat='courses:lesson_',
        )

    builder.adjust(1)

    return builder.as_markup()
