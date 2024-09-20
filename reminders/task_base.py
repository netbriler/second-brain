from django.utils.module_loading import import_string

from reminders.models import Reminder


class ReminderTaskBase:
    def __init__(self, reminder: Reminder, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reminder = reminder

    @staticmethod
    def get_task_class_from_str(task_class: str) -> type['ReminderTaskBase']:
        try:
            task_class = import_string(task_class)
        except (ModuleNotFoundError, ImportError):
            raise Exception(f'Task isn`t found in {task_class}')

        if not issubclass(task_class, ReminderTaskBase):
            raise TypeError(f'Class {task_class} isn`t instance of Task')

        return task_class

    @staticmethod
    def get_task_class_str(task_class: type['ReminderTaskBase']) -> str:
        return f'{task_class.__module__}.{task_class.__name__}'

    def run(self):
        raise NotImplementedError('Method run must be implemented in subclass')
