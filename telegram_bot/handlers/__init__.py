from aiogram import Router

from .admin import router as admin_router
from .users import router as users_router

router = Router(name='main')

router.include_routers(
    admin_router,
    users_router,
)
