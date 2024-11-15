import logging

from django.db import transaction
from django.utils.timezone import now

from workflows.constants import (
    JOB_ACTIVE,
    JOB_FAILED,
    JOB_PLANNED,
    JOB_SUCCESS,
    PROCESS_DONE,
    PROCESS_FAILED,
)
from workflows.models import Job, JobLog, Process, ProcessLog


class ContextualLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        if 'job' not in self.extra:
            return f'[Process: {self.extra["process"]}] {msg}', kwargs

        return f'[Process: {self.extra["process"]}] [Job: {self.extra["job"]}] {msg}', kwargs


class Workflow:
    default_stage = 'prepare'
    service_class = None

    def get_logger(self, process, job=None):
        logger = logging.getLogger(__name__)
        return ContextualLogger(logger, {'process': process, 'job': job})

    @transaction.atomic
    def create_job(
            self,
            process: Process,
            stage: str,
            data: dict = None,
            parents=None,
            status=JOB_ACTIVE,
    ) -> Job:
        assert hasattr(self, stage) and callable(getattr(self, stage))  # noqa: S101

        if parents is None:
            parents = []

        job = Job.objects.create(
            process=process,
            stage=stage,
            data=data or {},
            status=status,
        )

        job.parents.set(
            parents,
        )

        self.job_log(job, 'Job created')

        return job

    @transaction.atomic
    def activate_job(self, job):
        if job.status == JOB_ACTIVE:
            return
        job.status = JOB_ACTIVE
        job.save(
            update_fields=('status',),
        )
        self.job_log(job, 'Job activated')

    def check_process_done(self, job):
        if not Job.objects.filter(process=job.process).exclude(status__in=(JOB_SUCCESS, JOB_FAILED)).exists():
            # process done
            self.done_process(process=job.process, comment='All jobs done')

    @transaction.atomic
    def done_job(self, job: Job, disable_triggers=False):
        if job.status == JOB_SUCCESS:
            return

        if job.status == JOB_FAILED:
            raise Exception('Can not done failed job')

        job.status = JOB_SUCCESS
        job.done_at = now()
        job.save(
            update_fields=('status', 'done_at'),
        )

        self.job_log(job, 'Job done')

        if not disable_triggers:
            # trigger next jobs
            self.run_children(job)
            self.check_process_done(job)

    @transaction.atomic
    def run_children(self, job: Job):
        planned_children = job.children.filter(status=JOB_PLANNED).prefetch_related('parents')
        for child in planned_children:
            if all(parent.status == JOB_SUCCESS for parent in child.parents.all()):
                self.activate_job(child)

    @transaction.atomic
    def fail_job(self, job: Job, disable_triggers=False):
        if job.status == JOB_FAILED:
            return

        if job.status == JOB_SUCCESS:
            raise Exception('Can not fail done job')

        job.status = JOB_FAILED
        job.done_at = now()
        job.save(
            update_fields=('status', 'done_at'),
        )

        self.job_log(job, 'Job failed')

        for parent in job.parents.all():
            if parent.stage != self.default_stage:
                self.fail_job(parent, disable_triggers=disable_triggers)

        if not disable_triggers:
            self.check_process_done(job)

    @transaction.atomic
    def done_process(self, process: Process, job: Job = None, comment: str = None):
        if job and job.status not in (JOB_SUCCESS, JOB_FAILED):
            self.done_job(job, disable_triggers=True)

        process.status = PROCESS_DONE
        process.done_at = now()
        process.save(
            update_fields=('status', 'done_at'),
        )

        self.process_log(process, f'Process done: {comment}')

    @transaction.atomic
    def fail_process(self, process: Process, job: Job = None, comment: str = None):
        if job and job.status not in (JOB_SUCCESS, JOB_FAILED):
            self.fail_job(job, disable_triggers=True)

        process.status = PROCESS_FAILED
        process.done_at = now()
        process.save(
            update_fields=('status', 'done_at'),
        )

        self.process_log(process, f'Process failed: {comment}')

    @transaction.atomic
    def update_job_data(self, job: Job, data: dict):
        job.data = {**job.data, **data}
        job.save(
            update_fields=('data',),
        )

        self.job_log(job, f'Job data updated new data: {data}')

    def job_log(
            self,
            job: Job,
            message: str,
    ):
        logger = self.get_logger(job.process, job)
        logger.info(message)

        JobLog.objects.create(
            job=job,
            message=message,
        )

    def process_log(
            self,
            process: Process,
            message: str,
    ):
        logger = self.get_logger(process)
        logger.info(message)

        ProcessLog.objects.create(
            process=process,
            message=message,
        )


class AsyncWorkflow(Workflow):
    default_stage = 'prepare'
    service_class = None

    async def create_job(self, process: Process, stage: str, data: dict = None, parents=None, status=JOB_ACTIVE) -> Job:
        assert hasattr(self, stage) and callable(getattr(self, stage))  # noqa: S101
        if parents is None:
            parents = []
        job = await Job.objects.acreate(
            process=process,
            stage=stage,
            data=data or {},
            status=status,
        )
        await job.parents.aset(parents)
        await self.job_log(job, 'Job created')
        return job

    async def activate_job(self, job):
        if job.status == JOB_ACTIVE:
            return
        job.status = JOB_ACTIVE
        await job.asave(update_fields=('status',))
        await self.job_log(job, 'Job activated')

    async def check_process_done(self, job):
        if not await Job.objects.filter(process=job.process).exclude(status__in=(JOB_SUCCESS, JOB_FAILED)).aexists():
            await self.done_process(process=job.process, comment='All jobs done')

    async def done_job(self, job: Job, disable_triggers=False):
        if job.status == JOB_SUCCESS:
            return
        if job.status == JOB_FAILED:
            raise Exception('Cannot mark a failed job as done')
        job.status = JOB_SUCCESS
        job.done_at = now()
        await job.asave(update_fields=('status', 'done_at'))
        await self.job_log(job, 'Job done')
        if not disable_triggers:
            await self.run_children(job)
            await self.check_process_done(job)

    async def run_children(self, job: Job):
        async for child in job.children.filter(status=JOB_PLANNED).select_related('process').prefetch_related('parents'):
            if all(
                    parent.status == JOB_SUCCESS for parent in [p async for p in child.parents.all()]
            ):
                await self.activate_job(child)

    async def fail_job(self, job: Job, disable_triggers=False):
        if job.status == JOB_FAILED:
            return
        if job.status == JOB_SUCCESS:
            raise Exception('Cannot fail a completed job')
        job.status = JOB_FAILED
        job.done_at = now()
        await job.asave(update_fields=('status', 'done_at'))
        await self.job_log(job, 'Job failed')
        async for parent in job.parents.all():
            if parent.stage != self.default_stage:
                await self.fail_job(parent, disable_triggers=disable_triggers)
        if not disable_triggers:
            await self.check_process_done(job)

    async def done_process(self, process: Process, job: Job = None, comment: str = None):
        if job and job.status not in (JOB_SUCCESS, JOB_FAILED):
            await self.done_job(job, disable_triggers=True)
        process.status = PROCESS_DONE
        process.done_at = now()
        await process.asave(update_fields=('status', 'done_at'))
        await self.process_log(process, f'Process done: {comment}')

    async def fail_process(self, process: Process, job: Job = None, comment: str = None):
        if job and job.status not in (JOB_SUCCESS, JOB_FAILED):
            await self.fail_job(job, disable_triggers=True)
        process.status = PROCESS_FAILED
        process.done_at = now()
        await process.asave(update_fields=('status', 'done_at'))
        await self.process_log(process, f'Process failed: {comment}')

    async def update_job_data(self, job: Job, data: dict):
        job.data = {**job.data, **data}
        await job.asave(update_fields=('data',))
        await self.job_log(job, f'Job data updated with: {data}')

    async def job_log(self, job: Job, message: str):
        logger = self.get_logger(job.process, job)
        logger.info(message)
        await JobLog.objects.acreate(job=job, message=message)

    async def process_log(self, process: Process, message: str):
        logger = self.get_logger(process)
        logger.info(message)
        await ProcessLog.objects.acreate(process=process, message=message)
