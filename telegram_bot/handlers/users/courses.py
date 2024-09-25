import re
from contextlib import suppress
from typing import NoReturn

from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineQueryResultArticle,
    InlineQueryResultsButton,
    InputTextMessageContent,
    Message,
)
from django.db.models import Q
from django.utils.translation import gettext as _

from courses.helpers import seconds_to_time, time_to_seconds
from courses.models import Course, Group, Lesson, LessonEntity
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
from telegram_bot.services.files import get_message_duration, send_file_to_user
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
                text=_('📚 {course_title}').format(course_title=course.title),
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
                text=_('📁 {group_title}').format(group_title=group.title),
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
                text=_('📝 {lesson_title}').format(lesson_title=lesson.title),
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
        button=InlineQueryResultsButton(
            text=_('No courses found'),
            start_parameter='help',
        )
        if not results
        else None,
    )


class CourseForm(StatesGroup):
    start_learning = State()


@router.message(
    or_f(
        Regexp(r'^/start course_(?P<course_id>\d+)$'),
        Regexp(r'^/course_(?P<course_id>\d+)$'),
    ),
)
async def message_course(message: Message, regexp: re.Match, state: FSMContext) -> NoReturn:
    await state.set_state(CourseForm.start_learning)
    course_id = regexp.group('course_id')
    try:
        course = await Course.objects.aget(id=course_id)
        await message.answer(
            text=get_course_text(course),
            reply_markup=get_course_inline_markup(course),
        )
    except Course.DoesNotExist:
        await message.answer(
            text=_('Course id not found'),
        )

    await message.delete()


@router.message(
    or_f(
        Regexp(r'^/start group_(?P<group_id>\d+)$'),
        Regexp(r'^/group_(?P<group_id>\d+)$'),
    ),
)
async def message_group(message: Message, regexp: re.Match, state: FSMContext) -> NoReturn:
    await state.set_state(CourseForm.start_learning)
    group_id = regexp.group('group_id')
    try:
        group = await Group.objects.select_related('parent', 'course').aget(id=group_id)
        await message.answer(
            text=get_group_text(group),
            reply_markup=get_group_inline_markup(group),
        )
    except Group.DoesNotExist:
        await message.answer(
            text=_('Group id not found'),
        )

    await message.delete()


@router.message(
    or_f(
        Regexp(r'^/start lesson_(?P<lesson_id>\d+)$'),
        Regexp(r'^/lesson_(?P<lesson_id>\d+)$'),
    ),
)
async def message_lesson(message: Message, regexp: re.Match, user: User, state: FSMContext) -> NoReturn:
    await state.set_state(CourseForm.start_learning)
    lesson_id = regexp.group('lesson_id')
    try:
        lesson = await Lesson.objects.select_related('group', 'course').aget(id=lesson_id)
        await message.answer(
            text=get_lesson_text(lesson),
            reply_markup=get_lesson_inline_markup(lesson),
        )
        state_data = await state.get_data()
        lesson_entity_messages = state_data.get('lesson_entity_messages', {})
        async for lesson_entity in lesson.lesson_entities.select_related('file').all():
            if lesson_entity.file:
                lesson_entity_message_id, __ = await send_file_to_user(
                    bot=message.bot,
                    file=lesson_entity.file,
                    user=user,
                    caption=lesson_entity.content,
                )
            else:
                lesson_entity_message_id = (
                    await message.answer(
                        text=lesson_entity.content,
                    )
                ).message_id

            lesson_entity_messages[lesson_entity_message_id] = lesson_entity.id

        await state.update_data(
            {
                'lesson_id': regexp.group('lesson_id'),
                'lesson_entity_messages': lesson_entity_messages,
            },
        )
    except Lesson.DoesNotExist:
        await message.answer(
            text=_('Lesson id not found'),
        )

    await message.delete()


@router.message(
    CourseForm.start_learning,
    F.reply_to_message.content_type.in_(
        {
            ContentType.AUDIO,
            ContentType.VIDEO,
            ContentType.VIDEO_NOTE,
            ContentType.VOICE,
        },
    ),
    Regexp(r'^(((?P<hours>\d\d?):)?(?P<minutes>[0-5]?\d)?:)?(?P<seconds>[0-5]?\d)$'),
)
async def message_time(message: Message, regexp: re.Match, state: FSMContext) -> NoReturn:
    data = await state.get_data()
    lesson_entity_messages = data.get('lesson_entity_messages', {})
    lesson_entity_id = lesson_entity_messages.get(message.reply_to_message.message_id)
    if not lesson_entity_id:
        return await message.answer(
            text=_('Please reply to the lesson entity message'),
        )
    try:
        await LessonEntity.objects.select_related('lesson').aget(id=lesson_entity_id)
    except LessonEntity.DoesNotExist:
        return await message.answer(
            text=_('Lesson entity not found'),
        )

    seconds = time_to_seconds(
        int(regexp.group('hours') or 0),
        int(regexp.group('minutes') or 0),
        int(regexp.group('seconds') or 0),
    )
    if get_message_duration(message.reply_to_message) < seconds:
        return await message.answer(
            text=_('The duration of the content is less than the specified time'),
        )

    progress_message = await message.answer(
        text=f'Saved time: {seconds_to_time(seconds)}',
        reply_to_message_id=message.reply_to_message.message_id,
    )
    await message.delete()

    progress_messages = data.get('progres_messages', [])
    for progress_message_id in progress_messages:
        with suppress(Exception):
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=progress_message_id,
            )
    progress_messages.append(progress_message.message_id)
    await state.update_data(
        {
            'progres_messages': progress_messages,
        },
    )
