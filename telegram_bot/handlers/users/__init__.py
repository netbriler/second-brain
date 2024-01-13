from aiogram import Router

from .helpers import router as helpers_router
from .settings import router as settings_router
from .start import router as start_router

router = Router(name=__name__)

router.include_routers(
    start_router,
    settings_router,
    helpers_router,
)
