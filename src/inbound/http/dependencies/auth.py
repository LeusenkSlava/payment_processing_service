import secrets

from fastapi import Header, HTTPException, status

from src.main.config.settings import settings


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    """
    Проверяет заголовок X-API-Key.

    :param x_api_key: значение заголовка X-API-Key.
    :raises HTTPException: 401, если ключ неверный.
    """
    if not secrets.compare_digest(x_api_key, settings.app.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )
