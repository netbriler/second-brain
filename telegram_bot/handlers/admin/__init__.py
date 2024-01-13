from aiogram import Router

from .admin_menu import router as admin_menu_router

router = Router(name=__name__)

router.include_routers(
    admin_menu_router,
)
