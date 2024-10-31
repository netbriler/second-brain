from aiogram import Router

from .ai import router as ai_router
from .courses import router as lessons_router
from .helpers import router as helpers_router
from .restricted_downloader import router as restricted_downloader_router
from .settings import router as settings_router
from .start import router as start_router

router = Router(name=__name__)

router.include_routers(
    lessons_router,
    restricted_downloader_router,
    ai_router,
    start_router,
    settings_router,
    helpers_router,
)
