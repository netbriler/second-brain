from decimal import Decimal

from django.db import connection
from django.db.models import BigIntegerField, Model
from django.urls import reverse
from django.utils.html import format_html


def model_link(obj: Model):
    if not obj:
        return '-'

    url = reverse(
        f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change',  # noqa: SLF001
        args=[obj.pk],
    )
    return format_html(
        '<a href="{url}">{text}</a>',
        url=url,
        text=str(obj),
    )


class AutoIncrementalField(BigIntegerField):
    MAX_BIGINT = 9223372036854775807

    def __init__(self, *args, **kwargs):
        if kwargs.get('null'):
            raise ValueError('AutoIncrementalField cannot be null')
        if kwargs.get('default'):
            raise ValueError('AutoIncrementalField cannot have a default value')
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                'min_value': 0,
                'max_value': BigIntegerField.MAX_BIGINT,
                **kwargs,
            },
        )

    def db_type(self, connection):
        return 'bigint'

    def pre_save(self, model_instance, add):
        if getattr(model_instance, self.attname) is None:
            app_name = model_instance._meta.app_label  # noqa: SLF001
            model_name = model_instance._meta.model_name  # noqa: SLF001
            attname = self.attname
            sequence_name = f'{app_name}_{model_name}_{attname}_seq'

            # Check if sequence exists, if not, create it
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT EXISTS (SELECT 1 FROM pg_class WHERE relkind='S' AND relname='{sequence_name}')",
                    # noqa: S608
                )
                sequence_exists = cursor.fetchone()[0]

                if not sequence_exists:
                    cursor.execute(f'CREATE SEQUENCE {sequence_name} START WITH 1')

                cursor.execute(f"SELECT nextval('{sequence_name}')")
                sequence_value = cursor.fetchone()[0]
                setattr(model_instance, self.attname, sequence_value)
                return sequence_value
        return super().pre_save(model_instance, add)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'null' in kwargs:
            del kwargs['null']
        if 'blank' in kwargs:
            del kwargs['blank']
        if 'default' in kwargs:
            del kwargs['default']
        return name, path, args, kwargs


def trim_trailing_zeros(value, precision=8):
    """
    Formats the number with the given precision, then strips trailing zeros
    and removes a dangling decimal point if all decimals were zeros.
    """
    if value is None:
        return ''

    d = Decimal(value).quantize(Decimal(f"1.{'0' * precision}"))
    s = format(d, 'f').rstrip('0').rstrip('.')
    return s
