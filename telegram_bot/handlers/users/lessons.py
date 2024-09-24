import re
from typing import NoReturn

from aiogram import Router
from aiogram.types import (
    CallbackQuery,
    InlineQueryResultArticle,
    InlineQueryResultsButton,
    InputTextMessageContent,
)
from django.db.models import Q
from django.utils.translation import gettext as _

from courses.models import Course
from telegram_bot.filters.regexp import Regexp

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
