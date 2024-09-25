from aiogram.fsm.state import State, StatesGroup


class FilesAddForm(StatesGroup):
    add_file = State()
