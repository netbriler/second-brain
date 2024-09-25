from django.utils.translation import gettext as _

from courses.models import Course, Group, Lesson


def get_course_text(course: Course):
    return _('<b>Course Information</b>\n\n<b>Title:</b> {title}\n<b>Description:</b> {description}\n').format(
        title=course.title,
        id=course.id,
        description=course.description if course.description else _('No description provided'),
    )


def get_group_text(group: Group):
    return _('<b>Group Information</b>\n\n<b>Title:</b> {title}\n<b>Description:</b> {description}\n\n').format(
        title=group.title,
        id=group.id,
        description=group.description if group.description else _('No description provided'),
    )


def get_lesson_text(lesson: Lesson):
    return _('<b>Lesson Information</b>\n\n<b>Title:</b> {title}\n\n').format(
        title=lesson.title,
    )
