from aiogram import Router

from .ai import router as ai_router
from .helpers import router as helpers_router
from .settings import router as settings_router
from .start import router as start_router

router = Router(name=__name__)

router.include_routers(
    start_router,
    settings_router,
    ai_router,
    helpers_router,
)
