from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.timezone import now

from workflows.constants import (
    JOB_ACTIVE,
    JOB_FAILED,
    JOB_STATUSES,
    JOB_SUCCESS,
    PROCESS_ACTIVE,
    PROCESS_STATUSES,
)

# несколько ролей выдоб, автокомплит адресов и фии релатив
# выборка по инпутам и по общей сумме инпутов min/max


# запихнуть все аккаунты в одну транзакйию и разбить по transaction size
# account role and input roles
# валидация адресов в дестинатион стринг
class Process(models.Model):
    class Meta:
        verbose_name = 'Process'
        verbose_name_plural = 'Processes'

    workflow_class = models.CharField(
        max_length=150,
        editable=False,
    )

    config_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        null=True,
        editable=False,
    )

    config_id = models.BigIntegerField(
        null=True,
        editable=False,
    )

    config = GenericForeignKey(
        ct_field='config_type',
        fk_field='config_id',
    )

    data = models.JSONField(
        encoder=DjangoJSONEncoder,
        editable=False,
        null=True,
    )

    status = models.CharField(
        max_length=50,
        choices=PROCESS_STATUSES,
        default=PROCESS_ACTIVE,
    )

    done_at = models.DateTimeField(
        null=True,
        editable=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    def __str__(self):
        return f'#{self.id}/ {self.config}'


class Job(models.Model):
    class Meta:
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'

    process = models.ForeignKey(
        'workflows.Process',
        on_delete=models.PROTECT,
        editable=False,
        related_name='jobs',
    )

    stage = models.CharField(
        max_length=50,
        editable=False,
    )

    status = models.CharField(
        max_length=50,
        choices=JOB_STATUSES,
        default=JOB_ACTIVE,
    )

    data = models.JSONField(
        encoder=DjangoJSONEncoder,
        editable=False,
        default=dict,
    )

    parents = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='children',
        editable=False,
    )

    debounced_till = models.DateTimeField(
        null=True,
        blank=True,
    )

    done_at = models.DateTimeField(
        null=True,
        editable=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    touched_at = models.DateTimeField(
        default=now,
        editable=False,
        db_index=True,
        help_text='When last time is was ran. This helps to proceed jobs all round',
    )

    @property
    def is_active(self):
        return self.status == JOB_ACTIVE

    @property
    def is_done(self):
        return self.status in (JOB_SUCCESS, JOB_FAILED)

    @property
    def debounce(self):
        if self.debounced_till and self.debounced_till > now():
            return self.debounced_till - now()

    def __str__(self):
        return f'{self.stage} #{self.pk}'


class JobLog(models.Model):
    class Meta:
        verbose_name = 'Job log'
        verbose_name_plural = 'Job logs'

    job = models.ForeignKey(
        'workflows.Job',
        on_delete=models.CASCADE,
        related_name='logs',
    )

    message = models.TextField(
        editable=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    def __str__(self):
        return f'{self.job} - {self.message}'


class ProcessLog(models.Model):
    class Meta:
        verbose_name = 'Process log'
        verbose_name_plural = 'Process logs'

    process = models.ForeignKey(
        'workflows.Process',
        on_delete=models.CASCADE,
        related_name='logs',
    )

    message = models.TextField(
        editable=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    def __str__(self):
        return f'{self.process} - {self.message}'
