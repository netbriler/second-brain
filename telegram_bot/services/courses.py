from django.utils.translation import gettext as _

from courses.models import Course, Group, Lesson, LessonEntity
from courses.services import GroupLessonsStats, LessonsStats, get_stats_emoji
from telegram_bot.models import File


def get_course_text(course: Course, stats: LessonsStats = None) -> str:
    stats_text = ''
    if stats:
        stats_text = _('<b>Total Finished:</b> {progress_emoji}{finished_count}/{total_count} ({percent}%)').format(
            finished_count=stats.finished_count,
            total_count=stats.total_count,
            percent=stats.percent,
            progress_emoji=get_stats_emoji(stats),
        )
    return _(
        '<b>Course Information</b>\n\n<b>Title:</b> {title}\n<b>Description:</b> {description}\n\n{stats_text}',
    ).format(
        title=course.title,
        id=course.id,
        description=course.description if course.description else _('No description provided'),
        stats_text=stats_text,
    )


def get_course_stats_text(stats: LessonsStats) -> str:
    stats_text = _(
        '<b>Course Progress</b>\n<b>Total Finished:</b> {progress_emoji}'
        '{finished_count}/{total_count} ({percent}%)\n\n',
    ).format(
        finished_count=stats.finished_count,
        total_count=stats.total_count,
        percent=stats.percent,
        progress_emoji=get_stats_emoji(stats),
    )
    for group_stats in stats.groups.values():
        stats_text += _(
            '<b>Group: {title}</b>\n<b>Finished:</b> {progress_emoji}{finished_count}/{total_count} ({percent}%)\n\n',
        ).format(
            title=group_stats.group.title if group_stats.group else _('No group'),
            finished_count=group_stats.finished_count,
            total_count=group_stats.total_count,
            percent=group_stats.percent,
            progress_emoji=get_stats_emoji(group_stats),
        )

    return stats_text


def get_group_stats_text(stats: GroupLessonsStats) -> str:
    stats_text = _(
        '<b>Group Progress</b>\n<b>Total Finished:</b> {progress_emoji}'
        '{finished_count}/{total_count} ({percent}%)\n\n',
    ).format(
        finished_count=stats.finished_count,
        total_count=stats.total_count,
        percent=stats.percent,
        progress_emoji=get_stats_emoji(stats),
    )

    return stats_text


def get_group_text(group: Group, stats: GroupLessonsStats = None) -> str:
    stats_text = ''
    if stats:
        stats_text = _('<b>Total Finished:</b> {progress_emoji}{finished_count}/{total_count} ({percent}%)').format(
            finished_count=stats.finished_count,
            total_count=stats.total_count,
            percent=stats.percent,
            progress_emoji=get_stats_emoji(stats),
        )
    return _(
        '<b>Group Information</b>\n\n<b>Title:</b> {title}\n<b>Description:</b> {description}\n\n{stats_text}',
    ).format(
        title=group.title,
        id=group.id,
        description=group.description if group.description else _('No description provided'),
        stats_text=stats_text,
    )


def get_lesson_text(lesson: Lesson) -> str:
    return _('<b>Lesson Information</b>\n\n<b>Title:</b> {title}\n\n').format(
        title=lesson.title,
    )


async def create_lesson_entity_from_file(lesson: Lesson, file: File) -> LessonEntity:
    return await LessonEntity.objects.acreate(
        lesson=lesson,
        content=file.caption or '',
        file=file,
    )


def create_lesson_entity_from_file_sync(lesson: Lesson, file: File) -> LessonEntity:
    return LessonEntity.objects.create(
        lesson=lesson,
        content=file.caption or '',
        file=file,
    )


def create_lessons_from_files(files):
    first_position = len(files) * 2
    i = 1
    for file in files:
        title = (file.caption or '').strip().split('\n')[0]
        lesson = Lesson.objects.create(
            title=title,
            position=first_position - i,
        )
        create_lesson_entity_from_file_sync(lesson=lesson, file=file)
        i += 1
