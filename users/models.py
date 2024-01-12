from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, AbstractUser
from django.db import models

from users.validators import UnicodeUsernameValidator


class User(AbstractUser, PermissionsMixin):
    """
    A User class implementing a fully featured User model with
    admin-compliant permissions.

    Username and password are required. Other fields are optional.
    """

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def get_all_permissions(self, obj=None):
        return super().get_all_permissions(obj)

    username_validator = UnicodeUsernameValidator()

    is_active = models.BooleanField(
        verbose_name='Active',
        default=True,
        help_text='Designates whether this user should be treated as active. '
                  'Unselect this instead of deleting accounts.',
    )

    first_name = models.CharField(
        verbose_name='First Name',
        max_length=150,
        blank=True,
        editable=False,
    )

    last_name = models.CharField(
        verbose_name='Last Name',
        max_length=150,
        blank=True,
        editable=False,
    )

    telegram_id = models.BigIntegerField(
        null=True,
        unique=True,
        verbose_name='Telegram ID',
    )

    telegram_username = models.CharField(
        max_length=32,
        null=True,
        editable=False,
        db_index=True,
        verbose_name='Telegram Username',
    )

    telegram_is_active = models.BooleanField(
        default=True,
        editable=False,
        verbose_name='Telegram Is Active',
    )

    telegram_activity_at = models.DateTimeField(
        null=True,
        editable=False,
    )

    language_code = models.CharField(
        max_length=10,
        default='en',
        blank=True,
    )

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        return f'{self.first_name} {self.last_name}'.strip()
