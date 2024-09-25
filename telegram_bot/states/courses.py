from aiogram.fsm.state import State, StatesGroup


class CourseForm(StatesGroup):
    start_learning = State()
