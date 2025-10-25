import re
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
    get_next_lesson,
    get_stats_emoji,
)
from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.filters.regexp import Regexp
from telegram_bot.keyboards.default.courses import get_learning_session_keyboard
from telegram_bot.keyboards.default.default import get_default_markup
from telegram_bot.keyboards.inline.course import (
    get_course_inline_markup,
    get_group_inline_markup,
    get_lesson_entity_inline_markup,
    get_lesson_inline_markup,
    get_start_learning_inline_markup,
)
from telegram_bot.services.cleaner import add_message_to_clean, clean_messages
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


@router.inline_query(
    CourseForm.learning_session,
    Regexp(r'^courses:course_(?P<course_id>\d+)?$'),
)
async def inline_query_course(query: CallbackQuery, regexp: re.Match, user: User) -> NoReturn:
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
            stats = await get_course_lessons_progress(course_id=course.id, user_id=user.id)
            async for group in course.groups.all():
                results.append(
                    InlineQueryResultArticle(
                        id=str(group.id),
                        title=f'{get_stats_emoji(stats, group.id)} {group.title}',
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
                        title=f'{get_stats_emoji(stats, lesson_id=lesson.id)} {lesson.title}',
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


@router.inline_query(
    CourseForm.learning_session,
    Regexp(r'^courses:group_(?P<group_id>\d+)?$'),
)
async def inline_query_group(query: CallbackQuery, regexp: re.Match, user: User) -> NoReturn:
    group_id = regexp.group('group_id')
    results = []
    if group_id:
        try:
            group = await Group.objects.aget(id=group_id)
            button = InlineQueryResultsButton(
                text=_('📁 {group_title}').format(group_title=group.title),
                start_parameter=f'group_{group.id}',
            )
            stats = await get_group_lessons_progress(group_id=group.id, user_id=user.id)
            async for lesson in group.lessons.all():
                results.append(
                    InlineQueryResultArticle(
                        id=str(lesson.id),
                        title=f'{get_stats_emoji(stats, lesson_id=lesson.id)} {lesson.title}',
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


@router.inline_query(
    CourseForm.learning_session,
    Regexp(r'^courses:lesson_(?P<lesson_id>\d+)?$'),
)
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
    CourseForm.learning_session,
    Regexp(r'^courses:course_(?P<course_id>\d+):stats$'),
)
async def callback_course_stats(
        callback_query: CallbackQuery,
        regexp: re.Match,
        user: User,
        state: FSMContext,
) -> NoReturn:
    course_id = regexp.group('course_id')
    try:
        course = await Course.objects.prefetch_related('groups').aget(id=course_id)
        stats = await get_course_lessons_progress(course_id=course.id, user_id=user.id)

        answer_message = await callback_query.message.answer(
            text=get_course_stats_text(stats),
            reply_markup=get_learning_session_keyboard(),
        )
        await add_message_to_clean(state, answer_message.message_id)
        await callback_query.answer()
    except Course.DoesNotExist:
        await callback_query.answer(
            text=_('Course id not found'),
        )


@router.inline_query(
    CourseForm.learning_session,
    Regexp(r'^courses:(?P<query>.+)?$'),
)
async def inline_query(query: CallbackQuery, regexp: re.Match, user: User) -> NoReturn:
    search_query = regexp.group('query') or ''
    results = list()
    middle_results = list()
    end_results = list()
    async for course in Course.objects.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query),
    ):
        stats = await get_course_lessons_progress(course_id=course.id, user_id=user.id)
        article = InlineQueryResultArticle(
            id=str(course.id),
            title=f'{get_stats_emoji(stats)} {course.title}',
            description=course.description,
            input_message_content=InputTextMessageContent(
                message_text=f'/start course_{course.id}',
            ),
        )
        if stats and stats.percent == 100:
            end_results.append(article)
        elif stats and stats.in_progress_count:
            middle_results.append(article)
        else:
            results.append(article)

    results.extend(middle_results)
    results.extend(end_results)

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
    CourseForm.learning_session,
    Regexp(r'^courses:group_(?P<group_id>\d+):stats$'),
)
async def callback_group_stats(
        callback_query: CallbackQuery,
        regexp: re.Match,
        user: User,
        state: FSMContext,
) -> NoReturn:
    group_id = regexp.group('group_id')
    try:
        group = await Group.objects.select_related('course').aget(id=group_id)
        stats = await get_group_lessons_progress(group_id=group.id, user_id=user.id)

        answer_message = await callback_query.message.answer(
            text=get_group_stats_text(stats),
            reply_markup=get_learning_session_keyboard(),
        )
        await add_message_to_clean(state, answer_message.message_id)
        await callback_query.answer()
    except Group.DoesNotExist:
        await callback_query.answer(
            text=_('Group id not found'),
        )


async def check_learning_session(
        message: Message,
        state: FSMContext,
        lesson_selected: bool = False,
        send_keyboard: bool = False,
        view: str = None,
) -> FSMContext:
    if await state.get_state() != CourseForm.learning_session or send_keyboard:
        await state.set_state(CourseForm.learning_session)
        await message.answer(
            _('Learning session started 📚'),
            reply_markup=get_learning_session_keyboard(lesson_selected=lesson_selected),
        )
        # TODO: Create a new learning session in the database
    if view:
        await state.update_data(
            {
                'view': view,
            },
        )
    return state


@router.message(
    or_f(
        Regexp(r'^/start course_(?P<course_id>\d+)$'),
        Regexp(r'^/course_(?P<course_id>\d+)$'),
    ),
)
async def message_course(message: Message, regexp: re.Match, state: FSMContext, user: User) -> NoReturn:
    await check_learning_session(message, state, view='course')
    course_id = regexp.group('course_id')
    answer_message_id = None
    try:
        course = await Course.objects.select_related('thumbnail').prefetch_related('links').aget(id=course_id)
        stats = await get_course_lessons_progress(course_id=course.id, user_id=user.id)

        if course.thumbnail:
            answer_message_id, _ = await send_file_to_user(
                bot=message.bot,
                file=course.thumbnail,
                user=user,
                caption=get_course_text(course, stats),
                reply_markup=get_course_inline_markup(course),
            )
        else:
            answer_message = await message.answer(
                text=get_course_text(course, stats),
                reply_markup=get_course_inline_markup(course),
            )
            answer_message_id = answer_message.message_id
    except Course.DoesNotExist:
        answer_message = await message.answer(
            text=_('Course id not found'),
        )
        answer_message_id = answer_message.message_id

    await message.delete()
    await clean_messages(bot=message.bot, chat_id=message.chat.id, state=state)
    await add_message_to_clean(state, answer_message_id)


@router.message(
    or_f(
        Regexp(r'^/start group_(?P<group_id>\d+)$'),
        Regexp(r'^/group_(?P<group_id>\d+)$'),
    ),
)
async def message_group(message: Message, regexp: re.Match, state: FSMContext, user: User) -> NoReturn:
    await check_learning_session(message, state, view='group')
    group_id = regexp.group('group_id')
    answer_message_id = None
    try:
        group = await Group.objects.select_related('parent', 'course', 'thumbnail').prefetch_related('links').aget(
            id=group_id
        )
        stats = await get_group_lessons_progress(group_id=group.id, user_id=user.id)

        if group.thumbnail:
            answer_message_id, _ = await send_file_to_user(
                bot=message.bot,
                file=group.thumbnail,
                user=user,
                caption=get_group_text(group, stats),
                reply_markup=get_group_inline_markup(group),
            )
        else:
            answer_message = await message.answer(
                text=get_group_text(group, stats),
                reply_markup=get_group_inline_markup(group),
            )
            answer_message_id = answer_message.message_id
    except Group.DoesNotExist:
        answer_message = await message.answer(
            text=_('Group id not found'),
        )
        answer_message_id = answer_message.message_id

    await message.delete()
    await clean_messages(bot=message.bot, chat_id=message.chat.id, state=state)
    await add_message_to_clean(state, answer_message_id)


async def set_lesson(message: Message, lesson: Lesson, user: User, state: FSMContext) -> list[int]:
    await check_learning_session(message, state, lesson_selected=True, view='lesson')

    answer_messages_ids = []

    if lesson.thumbnail:
        answer_message_id, _ = await send_file_to_user(
            bot=message.bot,
            file=lesson.thumbnail,
            user=user,
            caption=get_lesson_text(lesson),
            reply_markup=get_lesson_inline_markup(lesson),
        )
        answer_messages_ids.append(answer_message_id)
    else:
        answer_message = await message.answer(
            text=get_lesson_text(lesson),
            reply_markup=get_lesson_inline_markup(lesson),
        )
        answer_messages_ids.append(answer_message.message_id)
    state_data = await state.get_data()
    lesson_entity_messages = state_data.get('lesson_entity_messages', {})
    reply_markup_set = False
    async for lesson_entity in lesson.lesson_entities.select_related('file').prefetch_related('links').all():
        if lesson_entity.links:
            reply_markup = get_lesson_entity_inline_markup(lesson_entity)
        else:
            reply_markup = get_learning_session_keyboard(lesson_selected=True)
            reply_markup_set = True

        if lesson_entity.file:
            lesson_entity_message_id, __ = await send_file_to_user(
                bot=message.bot,
                file=lesson_entity.file,
                user=user,
                caption=lesson_entity.content,
                reply_markup=reply_markup,
            )
        else:
            lesson_entity_message_id = (
                await message.answer(
                    text=lesson_entity.content,
                    reply_markup=reply_markup,
                )
            ).message_id

        progress = await get_last_actual_progress(
            user=user,
            course=lesson.course,
            lesson=lesson,
            lesson_entity=lesson_entity,
        )
        if progress and progress.timecode:
            progress_message = await message.answer(
                text=_('Saved time: {time}').format(
                    time=seconds_to_time(progress.timecode),
                ),
                reply_to_message_id=lesson_entity_message_id,
                reply_markup=get_learning_session_keyboard(lesson_selected=True),
            )
            answer_messages_ids.append(progress_message.message_id)

        lesson_entity_messages[str(lesson_entity_message_id)] = str(lesson_entity.id)
        answer_messages_ids.append(lesson_entity_message_id)

    if not reply_markup_set:
        menu_message = await message.answer(
            text=_('Menu 📚'),
            reply_markup=get_learning_session_keyboard(lesson_selected=True),
        )
        answer_messages_ids.append(menu_message.message_id)

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

    return answer_messages_ids


@router.callback_query(
    CourseForm.learning_session,
    Regexp(r'^courses:lesson_(?P<lesson_id>\d+)$'),
)
async def callback_lesson(callback_query: CallbackQuery, regexp: re.Match, user: User, state: FSMContext) -> NoReturn:
    lesson_id = regexp.group('lesson_id')
    try:
        lesson = await (
            Lesson.objects.select_related('group', 'course', 'thumbnail')
            .prefetch_related('links').aget(id=lesson_id)
        )
        answer_messages_ids = await set_lesson(callback_query.message, lesson, user, state)
        for answer_messages_id in answer_messages_ids:
            await add_message_to_clean(state, answer_messages_id)
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
    state = await check_learning_session(message, state, lesson_selected=True, view='lesson')
    lesson_id = regexp.group('lesson_id')
    try:
        lesson = await Lesson.objects.select_related('group', 'course', 'thumbnail').prefetch_related('links').aget(
            id=lesson_id
        )
        answer_messages_ids = await set_lesson(message, lesson, user, state)
    except Lesson.DoesNotExist:
        answer_message = await message.answer(
            text=_('Lesson id not found'),
        )
        answer_messages_ids = [answer_message.message_id]

    await message.delete()
    await clean_messages(bot=message.bot, chat_id=message.chat.id, state=state)
    for answer_messages_id in answer_messages_ids:
        await add_message_to_clean(state, answer_messages_id)


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
        answer_message = await message.answer(
            text=_('Please reply to the lesson entity message'),
        )
        return await add_message_to_clean(state, answer_message.message_id)
    try:
        lesson_entry = await LessonEntity.objects.select_related('lesson', 'lesson__course').aget(
            id=int(lesson_entity_id),
        )
    except LessonEntity.DoesNotExist:
        answer_message = await message.answer(
            text=_('Lesson entity not found'),
        )
        return await add_message_to_clean(state, answer_message.message_id)

    seconds = time_to_seconds(
        int(regexp.group('hours') or 0),
        int(regexp.group('minutes') or 0),
        int(regexp.group('seconds') or 0),
    )
    if get_message_duration(message.reply_to_message) < seconds:
        answer_message = await message.answer(
            text=_('The duration of the content is less than the specified time'),
        )
        return await add_message_to_clean(state, answer_message.message_id)

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
    await clean_messages(bot=message.bot, state=state, chat_id=message.chat.id, key='progress_messages')
    await add_message_to_clean(state, progress_message.message_id, key='progress_messages')
    await add_message_to_clean(state, progress_message.message_id)


@router.message(
    CourseForm.learning_session,
    or_f(
        Command(commands=['stop_learning_session']),
        I18nText(_('Stop learning session 🛑')),
    ),
)
async def message_stop_learning_session(message: Message, user: User, state: FSMContext) -> NoReturn:
    await message.answer(
        _('Learning session stopped 📚'),
        reply_markup=get_default_markup(user),
    )

    await add_message_to_clean(state, message.message_id)
    await clean_messages(bot=message.bot, chat_id=message.chat.id, state=state)
    await state.clear()


@router.message(
    CourseForm.learning_session,
    or_f(
        Command(commands=['finish_current_lesson']),
        I18nText(_('Finish current lesson ✅')),
    ),
)
async def message_finish_current_lesson(message: Message, state: FSMContext, user: User) -> NoReturn:
    data = await state.get_data()
    view = data.get('view', None)
    if view != 'lesson':
        answer_message = await message.answer(
            _('Please select the lesson to finish'),
        )
        return await add_message_to_clean(state, answer_message.message_id)

    lesson_id = data.get('lesson_id')
    if not lesson_id:
        answer_message = await message.answer(
            _('Lesson not found'),
        )
        return await add_message_to_clean(state, answer_message.message_id)

    answer_messages_ids = []
    try:
        lesson = await Lesson.objects.select_related('course', 'group').prefetch_related('links').aget(id=lesson_id)

        await create_or_update_learning_progress(
            user=user,
            course=lesson.course,
            lesson=lesson,
            is_finished=True,
        )

        next_lesson, stats = await get_next_lesson(user, lesson)
        answer_message = await message.answer(
            _('Lesson finished ✅'),
            reply_markup=get_learning_session_keyboard(lesson_selected=bool(next_lesson)),
        )
        answer_messages_ids.append(answer_message.message_id)
        if not next_lesson:
            if stats and stats.percent == 100:
                answer_message = await message.answer(
                    _('All lessons in this course are completed ✅'),
                    reply_markup=get_start_learning_inline_markup(),
                )
                answer_messages_ids.append(answer_message.message_id)
            else:
                answer_message = await message.answer(
                    _('No more lessons in this group\nPlease select another group or course'),
                    reply_markup=get_lesson_inline_markup(lesson),
                )
                answer_messages_ids.append(answer_message.message_id)
        else:
            lesson_messages_ids = await set_lesson(message, next_lesson, user, state)
            answer_messages_ids += lesson_messages_ids
    except Lesson.DoesNotExist:
        answer_message = await message.answer(
            _('Lesson not found'),
        )
        answer_messages_ids.append(answer_message.message_id)

    await message.delete()
    await clean_messages(bot=message.bot, chat_id=message.chat.id, state=state)
    for answer_messages_id in answer_messages_ids:
        await add_message_to_clean(state, answer_messages_id)


# Start learning 📚
@router.message(
    or_f(
        Command(commands=['start_learning']),
        I18nText(_('Start learning 📚')),
    ),
)
async def message_start_learning(message: Message, state: FSMContext, user: User) -> NoReturn:
    await check_learning_session(message, state, send_keyboard=True, view='start_learning')

    latest_process = await get_last_actual_progress(user)

    answer_message = await message.answer(
        _('Please select the course, group or lesson to start learning'),
        reply_markup=get_start_learning_inline_markup(latest_process.lesson if latest_process else None),
    )

    await message.delete()
    await clean_messages(bot=message.bot, chat_id=message.chat.id, state=state)
    await add_message_to_clean(state, answer_message.message_id)
