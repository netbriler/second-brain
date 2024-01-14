from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from courses import models


class CourseGroupInline(admin.TabularInline):
    model = models.Course.groups.through
    extra = 1
    verbose_name = _('Course')
    verbose_name_plural = _('Courses')


class LessonGroupInline(admin.TabularInline):
    model = models.Lesson.groups.through
    extra = 1
    verbose_name = _('Lesson')
    verbose_name_plural = _('Lessons')


class GroupCourseInline(admin.TabularInline):
    model = models.Course.groups.through
    extra = 1
    verbose_name = _('Group')
    verbose_name_plural = _('Groups')
