from courses.models import Course, LearningProgress, Lesson, LessonEntity
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
        return await LearningProgress.objects.filter(
            user=user,
            **kwargs,
        ).alatest('updated_at')
    except LearningProgress.DoesNotExist:
        return None
