import re
from typing import NoReturn

from aiogram import Router
from aiogram.filters import or_f
from aiogram.types import (
    CallbackQuery,
    InlineQueryResultArticle,
    InlineQueryResultsButton,
    InputTextMessageContent,
    Message,
)
from django.db.models import Q
from django.utils.translation import gettext as _

from courses.models import Course, Group, Lesson
from telegram_bot.filters.regexp import Regexp
from telegram_bot.keyboards.inline.course import (
    get_course_inline_markup,
    get_group_inline_markup,
    get_lesson_inline_markup,
)
from telegram_bot.services.courses import (
    get_course_text,
    get_group_text,
    get_lesson_text,
)
from telegram_bot.services.files import send_file_to_user
from users.models import User

router = Router(name=__name__)


@router.inline_query(Regexp(r'^course_(?P<course_id>\d+)?$'))
async def inline_query_course(query: CallbackQuery, regexp: re.Match) -> NoReturn:
    course_id = regexp.group('course_id')
    results = []
    if course_id:
        try:
            course = await Course.objects.aget(id=course_id)
            button = InlineQueryResultsButton(
                text=_('Show {course_title}').format(course_title=course.title),
                start_parameter=f'course_{course.id}',
            )
            async for lesson in course.lessons.all():
                results.append(
                    InlineQueryResultArticle(
                        id=str(lesson.id),
                        title=lesson.title,
                        input_message_content=InputTextMessageContent(
                            message_text=f'/start lesson_{lesson.id}',
                        ),
                    ),
                )

        except Course.DoesNotExist:
            button = InlineQueryResultsButton(
                text=_('Course id not found'),
                start_parameter='help',
            )
    else:
        button = InlineQueryResultsButton(
            text=_('Enter course id after course_'),
            start_parameter='help',
        )

    await query.answer(
        results=results,
        cache_time=0,
        show_alert=True,
        button=button,
    )


@router.inline_query(Regexp(r'^group_(?P<group_id>\d+)?$'))
async def inline_query_group(query: CallbackQuery, regexp: re.Match) -> NoReturn:
    group_id = regexp.group('group_id')
    results = []
    if group_id:
        try:
            group = await Group.objects.aget(id=group_id)
            button = InlineQueryResultsButton(
                text=_('Show {group_title}').format(group_title=group.title),
                start_parameter=f'group_{group.id}',
            )
            async for lesson in group.lessons.all():
                results.append(
                    InlineQueryResultArticle(
                        id=str(lesson.id),
                        title=lesson.title,
                        input_message_content=InputTextMessageContent(
                            message_text=f'/start lesson_{lesson.id}',
                        ),
                    ),
                )

        except Group.DoesNotExist:
            button = InlineQueryResultsButton(
                text=_('Group id not found'),
                start_parameter='help',
            )
    else:
        button = InlineQueryResultsButton(
            text=_('Enter group id after group_'),
            start_parameter='help',
        )

    await query.answer(
        results=results,
        cache_time=0,
        show_alert=True,
        button=button,
    )


@router.inline_query(Regexp(r'^lesson_(?P<lesson_id>\d+)?$'))
async def inline_query_lesson(query: CallbackQuery, regexp: re.Match) -> NoReturn:
    lesson_id = regexp.group('lesson_id')
    results = []
    if lesson_id:
        try:
            lesson = await Lesson.objects.aget(id=lesson_id)
            button = InlineQueryResultsButton(
                text=_('Show {lesson_title}').format(lesson_title=lesson.title),
                start_parameter=f'lesson_{lesson.id}',
            )

        except Lesson.DoesNotExist:
            button = InlineQueryResultsButton(
                text=_('Lesson id not found'),
                start_parameter='help',
            )
    else:
        button = InlineQueryResultsButton(
            text=_('Enter lesson id after lesson_'),
            start_parameter='help',
        )

    await query.answer(
        results=results,
        cache_time=0,
        show_alert=True,
        button=button,
    )


@router.inline_query()
async def inline_query(query: CallbackQuery) -> NoReturn:
    results = list()
    async for course in Course.objects.filter(
        Q(title__icontains=query.query) | Q(description__icontains=query.query),
    ):
        results.append(
            InlineQueryResultArticle(
                id=str(course.id),
                title=course.title,
                description=course.description,
                input_message_content=InputTextMessageContent(
                    message_text=f'/start course_{course.id}',
                ),
            ),
        )

    await query.answer(
        results=results,
        cache_time=0,
        show_alert=True,
        button=InlineQueryResultsButton(
            text=_('No courses found'),
            start_parameter='help',
        )
        if not results
        else None,
    )


@router.message(
    or_f(
        Regexp(r'^/start course_(?P<course_id>\d+)$'),
        Regexp(r'^/course_(?P<course_id>\d+)$'),
    ),
)
async def message_course(message: Message, regexp: re.Match) -> NoReturn:
    course_id = regexp.group('course_id')
    try:
        course = await Course.objects.aget(id=course_id)
        await message.answer(
            text=get_course_text(course),
            show_alert=True,
            reply_markup=get_course_inline_markup(course),
        )
    except Course.DoesNotExist:
        await message.answer(
            text=_('Course id not found'),
            show_alert=True,
        )


@router.message(
    or_f(
        Regexp(r'^/start group_(?P<group_id>\d+)$'),
        Regexp(r'^/group_(?P<group_id>\d+)$'),
    ),
)
async def message_group(message: Message, regexp: re.Match) -> NoReturn:
    group_id = regexp.group('group_id')
    try:
        group = await Group.objects.select_related('parent', 'course').aget(id=group_id)
        await message.answer(
            text=get_group_text(group),
            show_alert=True,
            reply_markup=get_group_inline_markup(group),
        )
    except Group.DoesNotExist:
        await message.answer(
            text=_('Group id not found'),
            show_alert=True,
        )


@router.message(
    or_f(
        Regexp(r'^/start lesson_(?P<lesson_id>\d+)$'),
        Regexp(r'^/lesson_(?P<lesson_id>\d+)$'),
    ),
)
async def message_lesson(message: Message, regexp: re.Match, user: User) -> NoReturn:
    lesson_id = regexp.group('lesson_id')
    try:
        lesson = await Lesson.objects.select_related('group', 'course').aget(id=lesson_id)
        await message.answer(
            text=get_lesson_text(lesson),
            show_alert=True,
            reply_markup=get_lesson_inline_markup(lesson),
        )
        async for lesson_entity in lesson.lesson_entities.select_related('file').all():
            if lesson_entity.file:
                await send_file_to_user(
                    bot=message.bot,
                    file=lesson_entity.file,
                    user=user,
                    caption=lesson_entity.content,
                )
            else:
                await message.answer(
                    text=lesson_entity.content,
                    show_alert=True,
                )
    except Lesson.DoesNotExist:
        await message.answer(
            text=_('Lesson id not found'),
            show_alert=True,
        )
