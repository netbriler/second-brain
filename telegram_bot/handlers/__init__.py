from aiogram import Router

from .users import router as users_router

router = Router(name='main')

router.include_routers(
    users_router,
)
