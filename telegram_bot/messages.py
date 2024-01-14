from django.utils.translation import gettext as _

from telegram_bot.commands.admin import get_admin_commands
from telegram_bot.commands.default import get_default_commands
from users.models import User


def get_help_text(user: User) -> str:
    if user.is_superuser:
        commands = get_admin_commands(user.language_code, with_categories=True)
    else:
        commands = get_default_commands(user.language_code, with_categories=True)

    text = _('Help 🆘') + '\n\n'
    for command in commands:
        if isinstance(command, str):
            text += f'{command}\n'
        else:
            text += f'<b>{command.command}</b> - {command.description}\n'

    return text
