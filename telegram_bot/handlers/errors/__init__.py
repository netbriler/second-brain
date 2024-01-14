from aiogram import Router

from .error_handler import router as error_handler_router

router = Router(name=__name__)

router.include_routers(
    error_handler_router,
)
