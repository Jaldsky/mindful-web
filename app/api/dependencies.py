from dataclasses import dataclass
from typing import Annotated
from uuid import UUID
from fastapi import Depends, Header, Path, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import ACCEPT_LANGUAGE_HEADER
from ..db.session.provider import Provider
from ..schemas.accept_language_header_schema import AcceptLanguageHeaderSchema
from ..db.types import DatabaseSession
from ..db.models.tables import User
from ..schemas.analytics import AnalyticsUsageRequestSchema
from ..schemas.auth import OAuthProviderPathSchema
from ..services.auth.exceptions import TokenMissingException, TokenInvalidException
from ..services.auth.access import authenticate_access_token, extract_user_id_from_access_token
from ..services.auth.common import decode_token
from ..services.auth.constants import AUTH_ACCESS_COOKIE_NAME, AUTH_ANON_COOKIE_NAME
from ..services.auth.types import AccessToken

_bearer = HTTPBearer(auto_error=False)


def get_accept_language(
    request: Request,
    accept_language: Annotated[
        str,
        Header(alias=ACCEPT_LANGUAGE_HEADER, description="Локализация ответа запроса"),
    ] = "en",
) -> str:
    """Функция Dependency Injection для заголовка Accept-Language.

    Args:
        request: HTTP-запрос.
        accept_language: Значение заголовка Accept-Language.

    Returns:
        Нормализованная строка локали.
    """
    schema = AcceptLanguageHeaderSchema(accept_language=accept_language)
    request.state.locale = schema.accept_language
    return schema.accept_language


async def get_db_session() -> DatabaseSession:
    """Функция Dependency Injection предоставления сессии базы данных.

    Yields:
        Сессия SQLAlchemy для выполнения запросов.

    Raises:
        HTTPException: HTTP 500 Internal Server Error в случае сбоя при создании сессии.
    """
    async with Provider().async_manager.get_session() as session:
        yield session


def validate_usage_request_params(
    from_date: Annotated[
        str,
        Query(alias="from", description="Начало интервала (дата в формате DD-MM-YYYY)", example="05-04-2025"),
    ],
    to_date: Annotated[
        str,
        Query(alias="to", description="Конец интервала (дата в формате DD-MM-YYYY)", example="05-04-2025"),
    ],
    page: Annotated[int, Query(ge=1, description="Номер страницы", example=1)] = 1,
) -> AnalyticsUsageRequestSchema:
    """Dependency для валидации параметров запроса analytics usage."""
    return AnalyticsUsageRequestSchema(
        from_date=from_date,
        to_date=to_date,
        page=page,
    )


def get_oauth_provider_path(
    provider: str = Path(..., description="Имя OAuth-провайдера", example="google"),
) -> OAuthProviderPathSchema:
    """Функция извлечения {provider} из пути, нормализации и валидации.

    Args:
        provider: Имя OAuth-провайдера из path.

    Returns:
        OAuthProviderPathSchema с нормализованным полем provider.

    Raises:
        InvalidOAuthProviderFormatException: Если provider пустой после нормализации (422).
        ValidationError: Если provider не строка (422).
    """
    return OAuthProviderPathSchema(provider=provider)


def _extract_access_token(
    credentials: HTTPAuthorizationCredentials | None,
    request: Request,
) -> AccessToken | None:
    """Функция извлечения токена доступа из заголовка или куки.

    Args:
        credentials: Bearer-токен из заголовка Authorization.
        request: HTTP-запрос для доступа к куки.

    Returns:
        JWT токен доступа или None.
    """
    if credentials is not None:
        return credentials.credentials
    return request.cookies.get(AUTH_ACCESS_COOKIE_NAME)


def _extract_actor_token(
    credentials: HTTPAuthorizationCredentials | None,
    request: Request,
) -> AccessToken | None:
    """Функция извлечения токена доступа или анонимной сессии из заголовка или куки.

    Args:
        credentials: Bearer-токен из заголовка Authorization.
        request: HTTP-запрос для доступа к куки.

    Returns:
        JWT токен доступа или анонимной сессии или None.
    """
    if credentials is not None:
        return credentials.credentials
    return request.cookies.get(AUTH_ACCESS_COOKIE_NAME) or request.cookies.get(AUTH_ANON_COOKIE_NAME)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: DatabaseSession = Depends(get_db_session),
) -> User:
    """Функция получения текущего пользователя по JWT токену доступа (Bearer).

    Процесс проверки включает:
    1. Проверку наличия заголовка Authorization: Bearer <token>
    2. Декодирование JWT и проверку срока действия токена
    3. Проверку типа токена
    4. Извлечение user_id из поля sub
    5. Поиск пользователя в базе данных по user_id

    Args:
        request: HTTP-запрос.
        credentials: Bearer-токен из заголовка Authorization.
        db: Сессия базы данных.

    Returns:
        Текущий авторизованный пользователь.

    Raises:
        TokenMissingException: Если заголовок Authorization отсутствует.
        TokenInvalidException: Если токен невалиден/не access/содержит некорректный sub.
        TokenExpiredException: Если токен истёк.
        UserNotFoundException: Если пользователь не найден в системе.
    """
    token = _extract_access_token(credentials, request)
    if token is None:
        raise TokenMissingException(key="auth.errors.token_missing", fallback="Token is missing")

    return await authenticate_access_token(db, token)


async def get_current_user_id(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UUID:
    """Функция получения идентификатора текущего пользователя по JWT токену доступа.

    Args:
        request: HTTP-запрос.
        credentials: Bearer-токен из заголовка Authorization.

    Returns:
        UUID пользователя.

    Raises:
        TokenMissingException: Если заголовок Authorization отсутствует.
        TokenInvalidException: Если токен невалиден.
        TokenExpiredException: Если токен истёк.
    """
    token = _extract_access_token(credentials, request)
    if token is None:
        raise TokenMissingException(key="auth.errors.token_missing", fallback="Token is missing")

    return extract_user_id_from_access_token(token)


@dataclass(slots=True, frozen=True)
class ActorContext:
    """Контекст пользователя/анонимной сессии, полученный из JWT."""

    actor_id: UUID
    actor_type: str


async def get_actor_id_from_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: DatabaseSession = Depends(get_db_session),
) -> ActorContext:
    """Функция получения идентификатора пользователя/анонимной сессии из JWT.

    Поддерживает токены:
    - access: валидируется, пользователь должен существовать
    - anon: валидируется по подписи/TTL, возвращается anon_id из sub

    Args:
        request: HTTP-запрос.
        credentials: Bearer-токен из заголовка Authorization.
        db: Сессия базы данных.

    Returns:
        ActorContext с actor_id и actor_type (access/anon).

    Raises:
        TokenMissingException: Если заголовок Authorization отсутствует.
        TokenInvalidException: Если токен невалиден/не поддерживается/содержит некорректный sub.
        TokenExpiredException: Если токен истёк.
        UserNotFoundException: Если пользователь не найден в системе.
    """
    token = _extract_actor_token(credentials, request)
    if token is None:
        raise TokenMissingException(key="auth.errors.token_missing", fallback="Token is missing")

    payload = decode_token(token)
    token_type = payload.get("type")

    if token_type == "access":
        user = await authenticate_access_token(db, token)
        return ActorContext(actor_id=user.id, actor_type="access")

    if token_type == "anon":
        try:
            return ActorContext(actor_id=UUID(str(payload.get("sub"))), actor_type="anon")
        except (TypeError, ValueError):
            raise TokenInvalidException(key="auth.errors.token_invalid", fallback="Token is invalid")

    raise TokenInvalidException(key="auth.errors.token_invalid", fallback="Token is invalid")
