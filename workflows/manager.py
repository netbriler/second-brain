import logging
from datetime import timedelta
from time import sleep, time

from django.db import transaction
from django.db.models import Q
from django.utils.module_loading import import_string
from django.utils.timezone import now

from workflows.constants import JOB_ACTIVE
from workflows.models import Job, Process
from workflows.workflow import Workflow

DEFAULT_EXECUTION_TIMEOUT = 60


class Manager:
    def run(self, timeout=DEFAULT_EXECUTION_TIMEOUT, stop_on_jobs_end: bool = False):
        run_until = time() + timeout if timeout else None

        while True:
            if run_until and time() > run_until:
                break

            # this always select next job
            # so if any job created new one, then it will be executed almost immediately
            # ordered by touch mark
            job = (
                Job.objects.filter(
                    status=JOB_ACTIVE,
                )
                .filter(
                    Q(debounced_till__isnull=True) | Q(debounced_till__lte=now()),
                )
                .select_related(
                    'process',
                )
                .prefetch_related(
                    'parents',
                    'children',
                )
                .order_by(
                    'touched_at',
                )
                .first()
            )

            if not job:
                logging.info('No jobs')
                if stop_on_jobs_end:
                    return
                sleep(1)
                continue

            self.run_job(job)

            # touch job, this moves job to the end of queue
            # todo add triggers in loader to remo jons from queue without processing
            job.touched_at = now()
            job.save(update_fields=['touched_at'])

    def run_job(self, job: Job):
        workflow = self.get_workflow(job.process.workflow_class)

        try:
            with transaction.atomic():
                job = Job.objects.select_for_update().get(id=job.id)
                getattr(workflow, job.stage)(process=job.process, job=job)
        except Exception as err:
            logging.exception(err)

            # debounce job in case of unexpected error
            job.debounced_till = now() + timedelta(minutes=1)
            job.save(update_fields=['debounced_till'])

    def get_workflow(self, workflow_class) -> Workflow:
        try:
            workflow_class = import_string(workflow_class)
        except (ModuleNotFoundError, ImportError):
            raise Exception(f'Workflow isn`t found in {workflow_class}')

        workflow = workflow_class()

        if not isinstance(workflow, Workflow):
            raise TypeError(f'Class {workflow_class} isn`t instance of Workflow')

        return workflow

    def get_workflow_class(self, workflow_class) -> type[Workflow]:
        return self.get_workflow(workflow_class).__class__

    def get_workflow_class_str(self, workflow_class: Workflow) -> str:
        return f'{workflow_class.__module__}.{workflow_class.__name__}'

    @transaction.atomic()
    def create_process(self, config, workflow_class: Workflow, stage: str = None, stage_data: dict = None):
        process = Process.objects.create(
            workflow_class=self.get_workflow_class_str(workflow_class),
            config=config,
        )

        job = Job.objects.create(
            process=process,
            stage=stage or workflow_class.default_stage,
            data=stage_data or {},
            status=JOB_ACTIVE,  # first job always active
        )

        return process, job


manager = Manager()
