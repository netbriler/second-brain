import re
from contextlib import suppress
from typing import NoReturn

from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
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
from courses.services import (
    create_or_update_learning_progress,
    get_course_lessons_progress,
    get_group_lessons_progress,
    get_last_actual_progress,
)
from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.filters.regexp import Regexp
from telegram_bot.keyboards.default.courses import get_learning_session_keyboard
from telegram_bot.keyboards.default.default import get_default_markup
from telegram_bot.keyboards.inline.course import (
    get_course_inline_markup,
    get_group_inline_markup,
    get_lesson_inline_markup,
    get_start_learning_inline_markup,
)
from telegram_bot.services.courses import (
    get_course_stats_text,
    get_course_text,
    get_group_stats_text,
    get_group_text,
    get_lesson_text,
)
from telegram_bot.services.files import get_message_duration, send_file_to_user
from telegram_bot.states.courses import CourseForm
from users.models import User

router = Router(name=__name__)


@router.inline_query(Regexp(r'^courses:course_(?P<course_id>\d+)?$'))
async def inline_query_course(query: CallbackQuery, regexp: re.Match) -> NoReturn:
    course_id = regexp.group('course_id')
    results = []
    if course_id:
        try:
            course = await Course.objects.prefetch_related(
                'groups',
                'lessons',
            ).aget(id=course_id)
            button = InlineQueryResultsButton(
                text=_('📚 {course_title}').format(course_title=course.title),
                start_parameter=f'course_{course.id}',
            )
            async for group in course.groups.all():
                results.append(
                    InlineQueryResultArticle(
                        id=str(group.id),
                        title=group.title,
                        description=group.description,
                        input_message_content=InputTextMessageContent(
                            message_text=f'/start group_{group.id}',
                        ),
                    ),
                )

            async for lesson in course.lessons.filter(group__isnull=True):
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


@router.inline_query(Regexp(r'^courses:group_(?P<group_id>\d+)?$'))
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


@router.inline_query(Regexp(r'^courses:lesson_(?P<lesson_id>\d+)?$'))
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


@router.callback_query(
    Regexp(r'^courses:course_(?P<course_id>\d+):stats$'),
)
async def callback_course_stats(callback_query: CallbackQuery, regexp: re.Match, user: User) -> NoReturn:
    course_id = regexp.group('course_id')
    try:
        course = await Course.objects.prefetch_related('groups').aget(id=course_id)
        stats = await get_course_lessons_progress(course_id=course.id, user_id=user.id)

        await callback_query.message.answer(
            text=get_course_stats_text(stats),
        )
    except Course.DoesNotExist:
        await callback_query.answer(
            text=_('Course id not found'),
        )

    await callback_query.answer()


@router.inline_query(
    Regexp(r'^courses:(?P<query>.+)?$'),
)
async def inline_query(query: CallbackQuery, regexp: re.Match) -> NoReturn:
    search_query = regexp.group('query') or ''
    results = list()
    async for course in Course.objects.filter(
        Q(title__icontains=search_query) | Q(description__icontains=search_query),
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


@router.callback_query(
    Regexp(r'^courses:group_(?P<group_id>\d+):stats$'),
)
async def callback_group_stats(callback_query: CallbackQuery, regexp: re.Match, user: User) -> NoReturn:
    group_id = regexp.group('group_id')
    try:
        group = await Group.objects.select_related('course').aget(id=group_id)
        stats = await get_group_lessons_progress(group_id=group.id, user_id=user.id)

        await callback_query.message.answer(
            text=get_group_stats_text(stats),
        )
    except Group.DoesNotExist:
        await callback_query.answer(
            text=_('Group id not found'),
        )

    await callback_query.answer()


async def check_learning_session(message: Message, state: FSMContext, has_next_lesson: bool = True) -> FSMContext:
    if await state.get_state() != CourseForm.learning_session:
        await state.set_state(CourseForm.learning_session)
        await message.answer(
            _('Learning session started 📚'),
            reply_markup=get_learning_session_keyboard(has_next_lesson=has_next_lesson),
        )
        # TODO: Create a new learning session in the database
    return state


@router.message(
    or_f(
        Regexp(r'^/start course_(?P<course_id>\d+)$'),
        Regexp(r'^/course_(?P<course_id>\d+)$'),
    ),
)
async def message_course(message: Message, regexp: re.Match, state: FSMContext, user: User) -> NoReturn:
    await check_learning_session(message, state)
    course_id = regexp.group('course_id')
    try:
        course = await Course.objects.aget(id=course_id)
        stats = await get_course_lessons_progress(course_id=course.id, user_id=user.id)
        await message.answer(
            text=get_course_text(course, stats),
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
async def message_group(message: Message, regexp: re.Match, state: FSMContext, user: User) -> NoReturn:
    await check_learning_session(message, state)
    group_id = regexp.group('group_id')
    try:
        group = await Group.objects.select_related('parent', 'course').aget(id=group_id)
        stats = await get_group_lessons_progress(group_id=group.id, user_id=user.id)
        await message.answer(
            text=get_group_text(group, stats),
            reply_markup=get_group_inline_markup(group),
        )
    except Group.DoesNotExist:
        await message.answer(
            text=_('Group id not found'),
        )

    await message.delete()


async def set_lesson(message: Message, lesson: Lesson, user: User, state: FSMContext) -> NoReturn:
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

        progress = await get_last_actual_progress(
            user=user,
            course=lesson.course,
            lesson=lesson,
            lesson_entity=lesson_entity,
        )
        if progress and progress.timecode:
            await message.answer(
                text=_('Saved time: {time}').format(
                    time=seconds_to_time(progress.timecode),
                ),
                reply_to_message_id=lesson_entity_message_id,
            )

        lesson_entity_messages[str(lesson_entity_message_id)] = str(lesson_entity.id)

    await create_or_update_learning_progress(
        user=user,
        course=lesson.course,
        lesson=lesson,
    )

    await state.update_data(
        {
            'lesson_id': lesson.id,
            'lesson_entity_messages': lesson_entity_messages,
        },
    )


@router.callback_query(
    Regexp(r'^courses:lesson_(?P<lesson_id>\d+)$'),
)
async def callback_lesson(callback_query: CallbackQuery, regexp: re.Match, user: User, state: FSMContext) -> NoReturn:
    lesson_id = regexp.group('lesson_id')
    try:
        lesson = await Lesson.objects.select_related('group', 'course').aget(id=lesson_id)
        await set_lesson(callback_query.message, lesson, user, state)
    except Lesson.DoesNotExist:
        await callback_query.answer(
            text=_('Lesson id not found'),
        )

    await callback_query.message.delete()


@router.message(
    or_f(
        Regexp(r'^/start lesson_(?P<lesson_id>\d+)$'),
        Regexp(r'^/lesson_(?P<lesson_id>\d+)$'),
    ),
)
async def message_lesson(message: Message, regexp: re.Match, user: User, state: FSMContext) -> NoReturn:
    state = await check_learning_session(message, state)
    lesson_id = regexp.group('lesson_id')
    try:
        lesson = await Lesson.objects.select_related('group', 'course').aget(id=lesson_id)
        await set_lesson(message, lesson, user, state)
    except Lesson.DoesNotExist:
        await message.answer(
            text=_('Lesson id not found'),
        )

    await message.delete()


@router.message(
    CourseForm.learning_session,
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
async def message_time(message: Message, regexp: re.Match, state: FSMContext, user: User) -> NoReturn:
    data = await state.get_data()
    lesson_entity_messages = data.get('lesson_entity_messages', {})
    lesson_entity_id = lesson_entity_messages.get(str(message.reply_to_message.message_id))
    if not lesson_entity_id:
        return await message.answer(
            text=_('Please reply to the lesson entity message'),
        )
    try:
        lesson_entry = await LessonEntity.objects.select_related('lesson', 'lesson__course').aget(
            id=int(lesson_entity_id),
        )
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

    await create_or_update_learning_progress(
        user=user,
        lesson=lesson_entry.lesson,
        course=lesson_entry.lesson.course,
        lesson_entity=lesson_entry,
        timecode=seconds,
    )

    progress_message = await message.answer(
        text=_('Saved time: {time}').format(
            time=seconds_to_time(seconds),
        ),
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


@router.message(
    CourseForm.learning_session,
    or_f(
        Command(commands=['stop_learning_session']),
        I18nText(_('Stop learning session 🛑')),
    ),
)
async def message_stop_learning_session(message: Message, user: User, state: FSMContext) -> NoReturn:
    await state.clear()
    await message.answer(
        _('Learning session stopped 📚'),
        reply_markup=get_default_markup(user),
    )


@router.message(
    CourseForm.learning_session,
    or_f(
        Command(commands=['finish_current_lesson']),
        I18nText(_('Finish current lesson ✅')),
    ),
)
async def message_finish_current_lesson(message: Message, state: FSMContext, user: User) -> NoReturn:
    data = await state.get_data()
    lesson_id = data.get('lesson_id')
    if not lesson_id:
        return await message.answer(
            _('Lesson not found'),
        )

    try:
        lesson = await Lesson.objects.select_related('course', 'group').aget(id=lesson_id)

        await create_or_update_learning_progress(
            user=user,
            course=lesson.course,
            lesson=lesson,
            is_finished=True,
        )

        await message.answer(
            _('Lesson finished ✅'),
            reply_markup=get_learning_session_keyboard(),
        )

        next_lesson = (
            await Lesson.objects.filter(
                course=lesson.course,
                position__gt=lesson.position,
                group=lesson.group,
            )
            .order_by('position')
            .select_related(
                'course',
                'group',
            )
            .afirst()
        )
        if not next_lesson:
            return await message.answer(
                _('No more lessons in this group'),
                reply_markup=get_learning_session_keyboard(has_next_lesson=False),
            )
        else:
            await set_lesson(message, next_lesson, user, state)
    except Lesson.DoesNotExist:
        return await message.answer(
            _('Lesson not found'),
        )


# Start learning 📚
@router.message(
    or_f(
        Command(commands=['start_learning']),
        I18nText(_('Start learning 📚')),
    ),
)
async def message_start_learning(message: Message, state: FSMContext, user: User) -> NoReturn:
    await check_learning_session(message, state, has_next_lesson=False)

    latest_process = await get_last_actual_progress(user)

    await message.answer(
        _('Please select the course, group or lesson to start learning'),
        reply_markup=get_start_learning_inline_markup(latest_process.lesson if latest_process else None),
    )
