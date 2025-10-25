from aiogram.fsm.state import State, StatesGroup


class FilesAddForm(StatesGroup):
    add_file = State()


class LessonFilesAddForm(StatesGroup):
    add_file = State()
