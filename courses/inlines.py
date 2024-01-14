from django.contrib import admin

from courses import models


class CourseGroupInline(admin.TabularInline):
    model = models.Course.groups.through
    extra = 1


class LessonGroupInline(admin.TabularInline):
    model = models.Lesson.groups.through
    extra = 1


class GroupCourseInline(admin.TabularInline):
    model = models.Course.groups.through
    extra = 1
