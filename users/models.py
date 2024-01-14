from django.conf import settings
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.validators import UnicodeUsernameValidator


class User(AbstractUser, PermissionsMixin):
    """
    A User class implementing a fully featured User model with
    admin-compliant permissions.

    Username and password are required. Other fields are optional.
    """

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def get_all_permissions(self, obj=None):
        return super().get_all_permissions(obj)

    username_validator = UnicodeUsernameValidator()

    is_active = models.BooleanField(
        verbose_name=_('Active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
        ),
    )

    first_name = models.CharField(
        verbose_name=_('First Name'),
        max_length=150,
        blank=True,
        editable=False,
        null=True,
    )

    last_name = models.CharField(
        verbose_name=_('Last Name'),
        max_length=150,
        blank=True,
        editable=False,
        null=True,
    )

    telegram_id = models.BigIntegerField(
        null=True,
        unique=True,
        verbose_name=_('Telegram ID'),
    )

    telegram_username = models.CharField(
        max_length=32,
        null=True,
        editable=False,
        db_index=True,
        verbose_name=_('Telegram Username'),
    )

    telegram_is_active = models.BooleanField(
        default=True,
        editable=False,
        verbose_name=_('Telegram Is Active'),
    )

    telegram_activity_at = models.DateTimeField(
        verbose_name=_('Telegram Last Activity At'),
        null=True,
        editable=False,
    )

    language_code = models.CharField(
        verbose_name=_('Language Code'),
        max_length=10,
        default='en',
        blank=True,
        choices=settings.LANGUAGES,
    )

    @property
    def full_name(self) -> str:
        """
        Return the first_name plus the last_name, with a space in between.
        """
        return f'{self.first_name} {self.last_name or ""}'.strip()

    # @property
    # def language_label(self) -> str:
    #     for code, label in settings.LANGUAGES:
    #         if code == user_language_code:
    #             return label
    #     return None
