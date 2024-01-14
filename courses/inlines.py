from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from courses import models


class CustomTabularInline(admin.TabularInline):
    extra = 1

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if formfield:
            formfield.label = self.verbose_name_plural
        return formfield


class CourseGroupInline(CustomTabularInline):
    model = models.Course.groups.through
    extra = 1
    verbose_name = _('Course')
    verbose_name_plural = _('Courses')


class GroupLessonInline(CustomTabularInline):
    model = models.Lesson.groups.through
    extra = 1

    verbose_name = _('Lesson')
    verbose_name_plural = _('Lessons')


class GroupCourseInline(CustomTabularInline):
    model = models.Course.groups.through
    extra = 1
    verbose_name = _('Group')
    verbose_name_plural = _('Groups')


class LessonGroupInline(CustomTabularInline):
    model = models.Lesson.groups.through
    extra = 1
    verbose_name = _('Lesson')
    verbose_name_plural = _('Lessons')
