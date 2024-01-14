from django.utils import timezone

from users.models import User


async def get_or_create_telegram_user(
    telegram_id: int,
    first_name: str,
    last_name: str,
    telegram_username: str,
    language_code: str,
) -> User:
    user, created = await User.objects.aupdate_or_create(
        telegram_id=telegram_id,
        defaults={
            'telegram_username': telegram_username,
            'first_name': first_name,
            'last_name': last_name,
            'telegram_activity_at': timezone.now(),
            'telegram_is_active': True,
        },
    )
    if created:
        user.language_code = language_code
        await user.asave(
            update_fields=['language_code'],
        )

    return user
