from asgiref.sync import sync_to_async
from attr import dataclass
from django.db import connection

from courses.models import Course, Group, LearningProgress, Lesson, LessonEntity
from users.models import User


async def create_or_update_learning_progress(
        user: User,
        lesson: Lesson,
        course: Course = None,
        lesson_entity: LessonEntity = None,
        timecode: int = None,
        is_finished: bool = None,
) -> LearningProgress:
    # Define common filters based on whether lesson_entity is provided
    filters = {
        'user': user,
        'course': course,
        'lesson': lesson,
    }

    # Try to get the most recent learning progress entry
    if is_finished is not None:
        await LearningProgress.objects.filter(**filters).aupdate(
            is_finished=is_finished,
        )

    if lesson_entity:
        filters['lesson_entity'] = lesson_entity

    progress = await LearningProgress.objects.filter(**filters).order_by('-updated_at').afirst()

    if progress:
        # Update the existing entry with new values
        if timecode is not None:
            progress.timecode = timecode
        if is_finished is not None:
            progress.is_finished = is_finished
        await progress.asave()
        return progress
    else:
        # Create a new entry if none exists
        progress = await LearningProgress.objects.acreate(
            user=user,
            course=course,
            lesson=lesson,
            lesson_entity=lesson_entity,
            timecode=timecode or 0,
            is_finished=is_finished if is_finished is not None else False,
        )
        return progress


async def get_last_actual_progress(
        user: User,
        course: Course = None,
        lesson: Lesson = None,
        lesson_entity: LessonEntity = None,
) -> LearningProgress | None:
    kwargs = {
        key: value
        for key, value in {
            'course': course,
            'lesson': lesson,
            'lesson_entity': lesson_entity,
        }.items()
        if value is not None
    }

    try:
        return (
            await LearningProgress.objects.filter(
                user=user,
                **kwargs,
            )
            .select_related('lesson', 'lesson_entity', 'course', 'user')
            .alatest('updated_at')
        )
    except LearningProgress.DoesNotExist:
        return None


@dataclass
class GroupLessonsStats:
    group: Group | None
    finished_ids: list[int]
    in_progress_ids: list[int]
    unstarted_ids: list[int]

    @property
    def finished_count(self) -> int:
        return len(self.finished_ids)

    @property
    def in_progress_count(self) -> int:
        return len(self.in_progress_ids)

    @property
    def unstarted_count(self) -> int:
        return len(self.unstarted_ids)

    @property
    def total_count(self) -> int:
        return self.finished_count + self.in_progress_count + self.unstarted_count

    @property
    def percent(self) -> float:
        percent = self.finished_count / self.total_count if self.total_count else 0.0

        return round(percent * 100, 2)


@dataclass
class LessonsStats:
    finished_ids: list[int]
    in_progress_ids: list[int]
    unstarted_ids: list[int]

    @property
    def finished_count(self) -> int:
        return len(self.finished_ids)

    @property
    def in_progress_count(self) -> int:
        return len(self.in_progress_ids)

    @property
    def unstarted_count(self) -> int:
        return len(self.unstarted_ids)

    @property
    def total_count(self) -> int:
        return self.finished_count + self.in_progress_count + self.unstarted_count

    @property
    def percent(self) -> float:
        percent = self.finished_count / self.total_count if self.total_count else 0.0

        return round(percent * 100, 2)

    groups: dict[int, GroupLessonsStats]


async def get_course_lessons_progress(user_id: int, course_id: int) -> LessonsStats:
    def raw_sql():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                WITH lesson_progress AS (SELECT DISTINCT ON (l.id) l.group_id,
                                                                   l.id                            AS lesson_id,
                                                                   l.title                         AS lesson_title,
                                                                   COALESCE(lp.is_finished, false) AS is_finished,
                                                                   lp.updated_at                   AS updated_at,
                                                                   l.position
                                         FROM courses_lesson l
                                                  LEFT JOIN (SELECT lesson_id,
                                                                    is_finished,
                                                                    updated_at
                                                             FROM courses_learningprogress lp
                                                             WHERE lp.user_id = %s
                                                               AND lp.course_id = %s
                                                             ORDER BY lp.updated_at DESC) lp ON l.id = lp.lesson_id
                                         WHERE l.course_id = %s
                                         ORDER BY l.id)
                SELECT lesson_id,
                       group_id,
                       is_finished,
                       CASE
                           WHEN NOT is_finished AND updated_at IS NOT NULL THEN true
                           ELSE false
                           END AS is_in_progress
                FROM lesson_progress
                ORDER BY position;
                """,
                [user_id, course_id, course_id],
            )

            return cursor.fetchall()

    result = await sync_to_async(raw_sql)()

    groups = {group.id: group async for group in Group.objects.filter(course_id=course_id)}
    data = {}
    for lesson_id, group_id, is_finished, is_in_progress in result:
        group = groups.get(group_id)
        data.setdefault(
            group_id,
            GroupLessonsStats(
                group=group,
                finished_ids=[],
                in_progress_ids=[],
                unstarted_ids=[],
            ),
        )

        if is_finished:
            data[group_id].finished_ids.append(lesson_id)
        elif is_in_progress:
            data[group_id].in_progress_ids.append(lesson_id)
        else:
            data[group_id].unstarted_ids.append(lesson_id)

    return LessonsStats(
        finished_ids=sum((group.finished_ids for group in data.values()), []),
        in_progress_ids=sum((group.in_progress_ids for group in data.values()), []),
        unstarted_ids=sum((group.unstarted_ids for group in data.values()), []),
        groups=data,
    )


async def get_group_lessons_progress(user_id: int, group_id: int) -> GroupLessonsStats:
    def raw_sql():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                WITH lesson_progress AS (SELECT DISTINCT ON (l.id) l.group_id,
                                                                   l.id                            AS lesson_id,
                                                                   l.title                         AS lesson_title,
                                                                   lp.updated_at                   AS updated_at,
                                                                   COALESCE(lp.is_finished, false) AS is_finished
                                         FROM courses_lesson l
                                                  LEFT JOIN (SELECT lesson_id,
                                                                    is_finished,
                                                                    updated_at
                                                             FROM courses_learningprogress lp
                                                             WHERE lp.user_id = %s
                                                             ORDER BY lp.updated_at DESC) lp ON l.id = lp.lesson_id
                                         WHERE l.group_id = %s
                                         ORDER BY l.id)
                SELECT lesson_id,
                       group_id,
                       is_finished,
                       CASE
                           WHEN NOT is_finished AND updated_at IS NOT NULL THEN true
                           ELSE false
                           END AS is_in_progress
                FROM lesson_progress
                WHERE group_id = %s;
                """,
                [user_id, group_id, group_id],
            )

            return cursor.fetchall()

    result = await sync_to_async(raw_sql)()

    data = GroupLessonsStats(
        group=await Group.objects.aget(id=group_id),
        finished_ids=[],
        in_progress_ids=[],
        unstarted_ids=[],
    )
    for lesson_id, group_id, is_finished, is_in_progress in result:  # noqa: B007
        if is_finished:
            data.finished_ids.append(lesson_id)
        elif is_in_progress:
            data.in_progress_ids.append(lesson_id)
        else:
            data.unstarted_ids.append(lesson_id)

    return data


FINISHED_EMOJI = '✅'
IN_PROGRESS_EMOJI = '⏳'
UNSTARTED_EMOJI = '🔒'


def get_stats_emoji(
        stats: GroupLessonsStats | LessonsStats,
        group_id: int = None,
        lesson_id: int = None,
) -> str:
    if isinstance(stats, LessonsStats) and group_id:
        stats = stats.groups.get(group_id) if stats else None

    emoji = ''
    if stats:
        if lesson_id:
            if lesson_id in stats.finished_ids:
                emoji = FINISHED_EMOJI
            elif lesson_id in stats.in_progress_ids:
                emoji = IN_PROGRESS_EMOJI
            else:
                emoji = UNSTARTED_EMOJI
        elif stats.percent == 100:
            emoji = FINISHED_EMOJI
        elif not stats.finished_count and not stats.in_progress_count:
            emoji = UNSTARTED_EMOJI
        else:
            emoji = IN_PROGRESS_EMOJI

    return emoji


def get_progress_emoji(
        learning_progress: LearningProgress,
) -> str:
    if not learning_progress:
        return UNSTARTED_EMOJI

    if learning_progress.is_finished:
        return FINISHED_EMOJI

    return IN_PROGRESS_EMOJI


async def get_next_lesson(user: User, lesson: Lesson) -> tuple[Lesson | None, LessonsStats | None]:
    if lesson.group_id:
        stats = await get_group_lessons_progress(user.id, lesson.group_id)
    elif lesson.course_id:
        stats = await get_course_lessons_progress(user.id, lesson.course_id)
    else:
        return None, None

    return (
        await Lesson.objects.filter(
            course=lesson.course,
            group=lesson.group,
        )
        .exclude(
            id__in=stats.finished_ids,
        )
        .order_by('position')
        .select_related(
            'course',
            'group',
        )
        .afirst()
    ), stats
