from reminders.task_base import ReminderTaskBase
from telegram_bot.loader import get_sync_bot
from telegram_bot.models import File
from telegram_bot.services.files import sync_send_file_to_user


class TelegramReminderTask(ReminderTaskBase):
    def run(self):
        bot = get_sync_bot()

        file = File.objects.get(id=self.reminder.data.get('file_id')) if self.reminder.data.get('file_id') else None
        user = self.reminder.user
        if file:
            sync_send_file_to_user(bot, file, user, send_file_info=True)

        bot.send_message(
            chat_id=user.telegram_id,
            text=self.reminder.data.get('text'),
        )
