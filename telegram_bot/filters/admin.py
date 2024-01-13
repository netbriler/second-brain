from aiogram.filters import Filter
from aiogram.types import Message

from users.models import User


class IsAdmin(Filter):
    async def __call__(self, message: Message, user: User) -> bool:
        return user.is_superuser
