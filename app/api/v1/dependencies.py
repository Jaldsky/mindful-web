import logging
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Header, HTTPException, status

from ...db.session.provider import manager
from ...db.types import DatabaseSession

logger = logging.getLogger(__name__)


def get_user_id_from_header(
    x_user_id: Annotated[
        str | None,
        Header(
            alias="X-User-ID",
            description="Уникальный идентификатор пользователя (UUID4). "
            "Если не указан — создаётся временный анонимный профиль",
            example="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        ),
    ] = None,
) -> UUID:
    """Функция Dependency Injection для извлечения X-User-ID из HTTP-заголовка
    Зависимость извлекает X-User-ID из HTTP-заголовка.
    - Если заголовок отсутствует -> генерируется новый временный UUID4 (анонимный режим).
    - Если заголовок присутствует, но не является валидным UUID4 -> ошибка 400.
    - Поддерживается только UUID версии 4.

    Args:
        x_user_id: Значение HTTP-заголовка X-User-ID, переданное клиентом, None - пользователь анонимный.

    Returns:
        Валидный идентификатор пользователя UUID4.

    Raises:
        HTTPException: HTTP 400 Bad Request с соответствующим сообщением.
    """
    if x_user_id is None:
        return uuid4()

    try:
        user_uuid = UUID(x_user_id)
        if user_uuid.version != 4:
            raise ValueError("Not a UUID4")
        return user_uuid
    except (ValueError, AttributeError):
        message = "Invalid X-User-ID: must be a valid UUID4 string"
        logger.exception(message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


async def get_db_session() -> DatabaseSession:
    """Функция Dependency Injection предоставления сессии базы данных.

    Yields:
        Сессия SQLAlchemy для выполнения запросов.

    Raises:
        HTTPException: HTTP 500 Internal Server Error в случае сбоя при создании сессии.
    """
    try:
        async with manager.get_session() as session:
            yield session
    except Exception as e:
        logger.exception(f"Failed to create database session: {e}")
        message = "Failed to create database session"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
