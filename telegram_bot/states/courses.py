from aiogram.fsm.state import State, StatesGroup


class CourseForm(StatesGroup):
    learning_session = State()
