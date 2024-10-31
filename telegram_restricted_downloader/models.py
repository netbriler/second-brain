from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


class Account(models.Model):
    telegram_id = models.BigIntegerField(
        null=True,
        verbose_name=_('Telegram ID'),
    )

    name = models.CharField(
        max_length=255,
    )

    username = models.CharField(
        null=True,
        max_length=255,
    )

    phone = models.CharField(
        max_length=255,
    )

    encrypted_session_string = models.TextField(
        null=True,
        editable=False,
        verbose_name=_('Encrypted Session String'),
    )

    user = models.ForeignKey(
        'users.User',
        related_name='accounts',
        on_delete=models.CASCADE,
        verbose_name=_('User'),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
    )

    last_used_at = models.DateTimeField(
        null=True,
        verbose_name=_('Last Used At'),
    )

    @cached_property
    def session_string(self):
        if self.encrypted_session_string:
            return self.decrypt(self.encrypted_session_string)
        return None

    def set_session_string(self, session_string: str):
        self.encrypted_session_string = self.encrypt(session_string)

    @staticmethod
    def encrypt(session_string: str) -> str:
        """Encrypt the session string."""
        fernet = Fernet(settings.TELEGRAM_SESSION_SECRET_KEY.encode())
        return fernet.encrypt(session_string.encode()).decode()

    @staticmethod
    def decrypt(encrypted_session_string: str) -> str:
        """Decrypt the encrypted session string."""
        fernet = Fernet(settings.TELEGRAM_SESSION_SECRET_KEY.encode())
        return fernet.decrypt(encrypted_session_string.encode()).decode()

    @staticmethod
    def encode_session_string(session_string: str):
        return Account.encrypt(session_string)

    def __str__(self):
        return self.name
