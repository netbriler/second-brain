from django.contrib import admin
from django.template.defaulttags import now

from workflows import models
from workflows.constants import JOB_ACTIVE, JOB_SUCCESS, PROCESS_DONE
from workflows.manager import manager


class JobLogInline(admin.TabularInline):
    model = models.JobLog

    readonly_fields = (
        'created_at',
        'message',
    )

    fields = (
        'created_at',
        'message',
    )

    ordering = ('created_at',)

    extra = 0
    show_change_link = False
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ProcessLogInline(admin.TabularInline):
    model = models.ProcessLog

    readonly_fields = (
        'created_at',
        'message',
    )

    fields = (
        'created_at',
        'message',
    )

    ordering = ('created_at',)

    extra = 0
    show_change_link = False
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class JobInline(admin.TabularInline):
    model = models.Job

    readonly_fields = (
        'created_at',
        'stage',
        'status',
        'data',
        'debounce',
        'done_at',
        'data',
    )

    fields = (
        'created_at',
        'id',
        'stage',
        'status',
        'data',
        'debounce',
    )

    ordering = ('created_at',)

    extra = 0
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class JobsInline(admin.TabularInline):
    model = models.Job.parents.through
    fk_name = 'from_job'

    readonly_fields = (
        'from_job',
        'to_job',
    )

    fields = (
        'from_job',
        'to_job',
    )

    ordering = ('from_job',)

    extra = 0
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'workflow_class',
        'config',
        'status',
        'done_at',
    )

    list_select_related = ('config_type',)

    list_filter = (
        'status',
        'workflow_class',
    )

    search_fields = ('data',)

    readonly_fields = (
        'config',
        'data',
        'done_at',
    )

    inlines = (
        JobInline,
        ProcessLogInline,
    )

    actions = ('done_process',)

    @admin.action(description='Done Process (UNSAFE)')
    def done_process(self, request, queryset):
        for process in queryset:
            process.status = PROCESS_DONE
            process.done_at = now()
            process.save()

            models.Job.objects.filter(process=process, status=JOB_ACTIVE).update(status=JOB_SUCCESS)

    def has_add_permission(self, request):
        return False


@admin.register(models.Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'process',
        'stage',
        'debounce',
        'touched_at',
        'status',
    )

    list_select_related = ('process',)

    list_filter = (
        'status',
        'stage',
    )

    readonly_fields = (
        'created_at',
        'stage',
        'debounce',
        'debounced_till',
        'done_at',
        'process',
        'data',
        'touched_at',
    )

    inlines = (
        JobsInline,
        JobLogInline,
    )

    search_fields = ('data',)

    ordering = ('-created_at',)

    actions = (
        'reset_debounce',
        'run',
        'done',
        'fail',
    )

    @admin.action(description='Reset Debounce')
    def reset_debounce(self, request, queryset):
        for job in queryset:
            job.debounced_till = now()
            job.save()

    @admin.action(description='Run Job (UNSAFE)')
    def run(self, request, queryset):
        for job in queryset:
            manager.run_job(job.process, job)

    @admin.action(description='Done (UNSAFE)')
    def done(self, request, queryset):
        # todo run triggers
        for job in queryset:
            workflow = manager.get_workflow(job.process.workflow_class)

            workflow.done_job(job)

    @admin.action(description='Fail (UNSAFE)')
    def fail(self, request, queryset):
        for job in queryset:
            workflow = manager.get_workflow(job.process.workflow_class)

            workflow.fail_job(job)

    def has_add_permission(self, request):
        return False
