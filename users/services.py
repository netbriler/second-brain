from users.models import User


async def get_or_create_user(
        telegram_id: int,
        first_name: str,
        last_name: str,
        telegram_username: str,
        language_code: str
) -> User:
    user, _ = await User.objects.aupdate_or_create(
        telegram_id=telegram_id,
        defaults={
            'telegram_username': telegram_username,
            'first_name': first_name,
            'last_name': last_name,
            'language_code': language_code,
        }
    )

    return user
