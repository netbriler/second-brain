from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UserbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'telegram_bot'

    verbose_name = _('Telegram Bot')

    def ready(self):
        import telegram_bot.receivers  # noqa
