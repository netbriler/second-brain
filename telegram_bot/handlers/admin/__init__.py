from aiogram import Router

from .files import router as files_router
from .users import router as users_router

router = Router(name=__name__)

router.include_routers(
    users_router,
    files_router,
)
