from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CryptoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crypto'

    verbose_name = _('Crypto')

    def ready(self):
        import crypto.receivers  # noqa
