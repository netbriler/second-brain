from aiogram import Router

from .admin import router as admin_router
from .errors import router as errors_router
from .users import router as users_router

router = Router(name='main')

router.include_routers(
    errors_router,
    admin_router,
    users_router,
)
