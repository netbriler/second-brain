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
    timecode: int = 0,
    is_finished: bool = None,
) -> LearningProgress:
    # Define common filters based on whether lesson_entity is provided
    filters = {
        'user': user,
        'course': course,
        'lesson': lesson,
    }
    if lesson_entity:
        filters['lesson_entity'] = lesson_entity

    # Try to get the most recent learning progress entry
    progress = await LearningProgress.objects.filter(**filters).order_by('-updated_at').afirst()

    if progress:
        # Update the existing entry with new values
        if timecode:
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
            timecode=timecode,
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
    finished_count: int
    unfinished_count: int
    total_count: int


@dataclass
class LessonsStats:
    finished_count: int
    unfinished_count: int
    total_count: int

    groups: dict[int, GroupLessonsStats]


async def get_lessons_progress(user_id: int, course_id: int) -> LessonsStats:
    def raw_sql():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                            WITH lesson_progress AS (
                                SELECT DISTINCT ON (l.id) l.group_id,
                                                      l.id                            AS lesson_id,
                                                      l.title                         AS lesson_title,
                                                      COALESCE(lp.is_finished, false) AS is_finished
                                FROM courses_lesson l
                                         LEFT JOIN (SELECT lesson_id,
                                                           is_finished
                                                    FROM courses_learningprogress lp
                                                    WHERE lp.user_id = %s
                                                      AND lp.course_id = %s
                                                    ORDER BY lp.updated_at DESC) lp ON l.id = lp.lesson_id
                                WHERE l.course_id = %s
                                ORDER BY l.id
                            )
                            SELECT group_id,
                                   COUNT(CASE WHEN is_finished = true THEN 1 END) AS finished_count,
                                   COUNT(CASE WHEN is_finished = false THEN 1 END) AS unfinished_count
                            FROM lesson_progress
                            GROUP BY group_id
                            ORDER BY group_id;
                        """,
                [user_id, course_id, course_id],
            )

            return cursor.fetchall()

    result = await sync_to_async(raw_sql)()

    groups = {group.id: group async for group in Group.objects.filter(course_id=course_id)}
    data = {}
    for group_id, finished_count, unfinished_count in result:
        group = groups.get(group_id)
        data[int(group_id)] = GroupLessonsStats(
            group=group,
            finished_count=finished_count,
            unfinished_count=unfinished_count,
            total_count=finished_count + unfinished_count,
        )

    return LessonsStats(
        finished_count=sum(stats.finished_count for stats in data.values()),
        unfinished_count=sum(stats.unfinished_count for stats in data.values()),
        total_count=sum(stats.total_count for stats in data.values()),
        groups=data,
    )
