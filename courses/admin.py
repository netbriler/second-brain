from admin_auto_filters.filters import AutocompleteFilterFactory
from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from utils.helpers import model_link

from .forms import GroupAndCourseForm
from .inlines import GroupInline, LessonEntityInline, LessonInline, LinkInline
from .models import Course, Group, LearningProgress, Lesson, LessonEntity, Link


@admin.register(Course)
class CourseAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'title',
        'description',
        'lesson_count',
        'created_at',
        'updated_at',
    )

    search_fields = (
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
        'lesson_count',
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
                    'description',
                    'lesson_count',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    inlines = [GroupInline, LessonInline, LinkInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(lesson_count=Count('lessons'))

    def lesson_count(self, obj):
        return obj.lesson_count

    lesson_count.short_description = _('Lesson Count')


@admin.register(Group)
class GroupAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'title',
        'description',
        'parent_link',
        'course_link',
        'lesson_count',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'title',
        'description',
        'created_at',
        'updated_at',
    )

    autocomplete_fields = ('parent', 'course', 'thumbnail')
    list_select_related = ('parent', 'course', 'thumbnail')

    list_filter = (
        'id',
        'title',
        'description',
        AutocompleteFilterFactory(_('Parent'), 'parent'),
        AutocompleteFilterFactory(_('Course'), 'course'),
        ('parent', admin.EmptyFieldListFilter),
        ('course', admin.EmptyFieldListFilter),
        'created_at',
        'updated_at',
    )

    readonly_fields = (
        'id',
        'lesson_count',
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
                    'description',
                    'thumbnail',
                    'parent',
                    'course',
                    'lesson_count',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    inlines = [GroupInline, LessonInline, LinkInline]

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

    def parent_link(self, obj):
        return model_link(obj.parent)

    parent_link.short_description = _('Parent')

    def course_link(self, obj):
        return model_link(obj.course)

    course_link.short_description = _('Course')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(lesson_count=Count('lessons'))

    def lesson_count(self, obj):
        return obj.lesson_count

    lesson_count.short_description = _('Lesson Count')


@admin.register(Lesson)
class LessonAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'title',
        'group_link',
        'course_link',
        'entries_count',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'title',
        'created_at',
        'updated_at',
    )

    list_filter = (
        AutocompleteFilterFactory(_('Group'), 'group'),
        AutocompleteFilterFactory(_('Course'), 'course'),
        ('group', admin.EmptyFieldListFilter),
        ('course', admin.EmptyFieldListFilter),
        'created_at',
        'updated_at',
    )

    autocomplete_fields = ('group', 'course')
    list_select_related = ('group', 'course')

    readonly_fields = (
        'id',
        'entries_count',
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
                    'group',
                    'course',
                    'entries_count',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    inlines = [LessonEntityInline, LinkInline]

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

    def group_link(self, obj):
        return model_link(obj.group)

    group_link.short_description = _('Group')

    def course_link(self, obj):
        return model_link(obj.course)

    course_link.short_description = _('Course')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(entity_count=Count('lesson_entities'))

    def entries_count(self, obj):
        return obj.entity_count

    entries_count.short_description = _('Entries Count')


@admin.register(LessonEntity)
class LessonEntityAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'content_short',
        'lesson_link',
        'lesson_course_link',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'content',
    )

    def content_short(self, obj):
        return obj.content_short

    content_short.short_description = _('Short Content')

    inlines = [LinkInline]

    list_select_related = ('lesson', 'file', 'lesson__course')
    autocomplete_fields = ('lesson', 'file')

    list_filter = (
        AutocompleteFilterFactory(_('Lesson'), 'lesson'),
        AutocompleteFilterFactory(_('Course'), 'lesson__course'),
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
                    'lesson',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    ordering = ('position',)

    def lesson_course_link(self, obj):
        return model_link(obj.lesson.course)

    lesson_course_link.short_description = _('Course')

    def lesson_link(self, obj):
        return model_link(obj.lesson)


@admin.register(LearningProgress)
class LearningProgressAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'user_link',
        'course_link',
        'lesson_link',
        'lesson_entity_link',
        'timecode',
        'is_finished',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'timecode',
        'is_finished',
        'created_at',
        'updated_at',
    )

    autocomplete_fields = ('user', 'course', 'lesson', 'lesson_entity')

    list_filter = (
        AutocompleteFilterFactory(_('User'), 'user'),
        AutocompleteFilterFactory(_('Course'), 'course'),
        AutocompleteFilterFactory(_('Lesson'), 'lesson'),
        AutocompleteFilterFactory(_('Lesson Entity'), 'lesson_entity'),
        ('lesson_entity', admin.EmptyFieldListFilter),
        'is_finished',
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
                    'user',
                    'course',
                    'lesson',
                    'lesson_entity',
                    'timecode',
                    'is_finished',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    def user_link(self, obj):
        return model_link(obj.user)

    user_link.short_description = _('User')

    def course_link(self, obj):
        return model_link(obj.course)

    course_link.short_description = _('Course')

    def lesson_link(self, obj):
        if obj.lesson:
            return model_link(obj.lesson)
        return '-'

    lesson_link.short_description = _('Lesson')

    def lesson_entity_link(self, obj):
        if obj.lesson_entity:
            return model_link(obj.lesson_entity)
        return '-'

    lesson_entity_link.short_description = _('Lesson Entity')


@admin.register(Link)
class LinkAdmin(DjangoQLSearchMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'title',
        'url',
        'course_link',
        'group_link',
        'lesson_link',
        'lesson_entity_link',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'title',
        'url',
    )

    list_select_related = ('course', 'group', 'lesson', 'lesson_entity')
    autocomplete_fields = ('course', 'group', 'lesson', 'lesson_entity')

    list_filter = (
        AutocompleteFilterFactory(_('Course'), 'course'),
        AutocompleteFilterFactory(_('Group'), 'group'),
        AutocompleteFilterFactory(_('Lesson'), 'lesson'),
        AutocompleteFilterFactory(_('Lesson entry'), 'lesson_entity'),
        ('course', admin.EmptyFieldListFilter),
        ('group', admin.EmptyFieldListFilter),
        ('lesson', admin.EmptyFieldListFilter),
        ('lesson_entity', admin.EmptyFieldListFilter),
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
                    'title',
                    'url',
                    'course',
                    'group',
                    'lesson',
                    'lesson_entity',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    ordering = ('position',)

    def course_link(self, obj):
        if obj.course:
            return model_link(obj.course)
        return '-'

    course_link.short_description = _('Course')

    def group_link(self, obj):
        if obj.group:
            return model_link(obj.group)
        return '-'

    group_link.short_description = _('Group')

    def lesson_link(self, obj):
        if obj.lesson:
            return model_link(obj.lesson)
        return '-'

    lesson_link.short_description = _('Lesson')

    def lesson_entity_link(self, obj):
        if obj.lesson_entity:
            return model_link(obj.lesson_entity)
        return '-'

    lesson_entity_link.short_description = _('Lesson entry')
