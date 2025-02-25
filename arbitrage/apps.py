from django.apps import AppConfig

from django.utils.translation import gettext_lazy as _


class ArbitrageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'arbitrage'

    verbose_name = _('Arbitrage')

    def ready(self):
        import arbitrage.receivers  # noqa
