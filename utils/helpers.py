from django.db.models import Model
from django.urls import reverse
from django.utils.html import format_html


def model_link(obj: Model):
    url = reverse(
        f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change',  # noqa: SLF001
        args=[obj.pk],
    )
    return format_html(
        '<a href="{url}">{text}</a>',
        url=url,
        text=str(obj),
    )
