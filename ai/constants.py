from enum import Enum

from django.utils.translation import gettext_lazy as _


class AIMessageCategories(Enum):
    NOTES = 'notes', _('Notes')
    WORKOUT = 'workout', _('Workout')
    MEALS = 'meals', _('Meals')
    EXPENSES = 'expenses', _('Expenses')
    TASKS = 'tasks', _('Tasks')
    REMINDERS = 'reminders', _('Reminders')
    READING = 'reading', _('Reading')
    COURSES = 'courses', _('Courses')

    @property
    def label(self):
        return self.value[1]