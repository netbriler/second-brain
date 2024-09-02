from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai'

    verbose_name = _('AI')
