from admin_auto_filters.filters import AutocompleteFilterFactory
from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from .forms import GroupAndCourseForm
from .inlines import GroupInline, LessonEntityInline, LessonInline
from .models import Course, Group, Lesson, LessonEntity


@admin.register(Course)
class CourseAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'title',
        'description',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'id',
        'title',
        'description',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'id',
        'title',
        'description',
        'created_at',
        'updated_at',
    )

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )

    ordering = (
        'id',
        'position',
    )

    fieldsets = [
        (
            _('General'),
            {
                'fields': [
                    'id',
                    'title',
                    'description',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    inlines = [GroupInline, LessonInline]


@admin.register(Group)
class GroupAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'title',
        'description',
        'parent',
        'course',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'id',
        'title',
        'description',
        'parent',
        'course',
        'created_at',
        'updated_at',
    )

    autocomplete_fields = ('parent', 'course')
    list_select_related = ('parent', 'course')

    list_filter = (
        'id',
        'title',
        'description',
        AutocompleteFilterFactory(_('Parent'), 'parent'),
        AutocompleteFilterFactory(_('Course'), 'course'),
        'created_at',
        'updated_at',
    )

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )

    ordering = (
        'id',
        'position',
    )

    fieldsets = [
        (
            _('General'),
            {
                'fields': [
                    'id',
                    'title',
                    'description',
                    'parent',
                    'course',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    inlines = [GroupInline, LessonInline]

    action_form = GroupAndCourseForm
    actions = ['assign_group_and_course']

    @admin.action(description=_('Assign selected group or course to lessons'))
    def assign_group_and_course(self, request, queryset):
        selected_group = request.POST.get('group_field')
        selected_course = request.POST.get('course_field')
        if selected_group or selected_course:
            for obj in queryset:
                if selected_group:
                    obj.parent_id = selected_group
                if selected_course:
                    obj.course_id = selected_course
                obj.save()


@admin.register(Lesson)
class LessonAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'title',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'id',
        'title',
        'created_at',
        'updated_at',
    )

    list_filter = (
        AutocompleteFilterFactory(_('Group'), 'group'),
        AutocompleteFilterFactory(_('Course'), 'course'),
        'created_at',
        'updated_at',
    )

    autocomplete_fields = ('group', 'course')
    list_select_related = ('group', 'course')

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )

    ordering = ('position',)

    fieldsets = [
        (
            _('General'),
            {
                'fields': [
                    'id',
                    'title',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    inlines = [LessonEntityInline]

    action_form = GroupAndCourseForm
    actions = ['assign_group_and_course']

    @admin.action(description=_('Assign selected group or course to lessons'))
    def assign_group_and_course(self, request, queryset):
        selected_group = request.POST.get('group_field')
        selected_course = request.POST.get('course_field')
        if selected_group or selected_course:
            for obj in queryset:
                if selected_group:
                    obj.group_id = selected_group
                if selected_course:
                    obj.course_id = selected_course
                obj.save()


@admin.register(LessonEntity)
class LessonEntityAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'lesson',
        'content',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'id',
        'content',
    )

    list_select_related = ('lesson', 'file')
    autocomplete_fields = ('lesson', 'file')

    list_filter = (
        AutocompleteFilterFactory(_('Lesson'), 'lesson'),
        'created_at',
        'updated_at',
    )

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )

    fieldsets = [
        (
            _('General'),
            {
                'fields': [
                    'id',
                    'content',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    ordering = (
        'lesson',
        'position',
    )
