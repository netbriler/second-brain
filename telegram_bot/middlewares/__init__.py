from aiogram import Dispatcher


def setup_middleware(dp: Dispatcher):
    from .logging import LoggingMiddleware
    from .user import UsersMiddleware

    dp.update.middleware(LoggingMiddleware())
    dp.update.middleware(UsersMiddleware())
