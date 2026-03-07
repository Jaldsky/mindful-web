from starlette.responses import Response

from .constants import (
    AUTH_ACCESS_COOKIE_NAME,
    AUTH_ANON_COOKIE_NAME,
    AUTH_REFRESH_COOKIE_NAME,
    AUTH_COOKIE_PATH,
)
from ...config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    AUTH_COOKIE_HTTPONLY,
    AUTH_COOKIE_SECURE,
    JWT_ANON_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    AUTH_COOKIE_DOMAIN,
    AUTH_COOKIE_SAMESITE,
    OAUTH_STATE_COOKIE_EXPIRE_MINUTES,
)


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Функция установки JWT токена доступа и токена обновления в HTTP куки.

    Args:
        response: HTTP-ответ для установки куки.
        access_token: JWT токен доступа.
        refresh_token: JWT токен обновления.
    """
    cookie_domain = AUTH_COOKIE_DOMAIN or None
    cookie_path = AUTH_COOKIE_PATH or "/"
    samesite = AUTH_COOKIE_SAMESITE

    response.set_cookie(
        key=AUTH_ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=AUTH_COOKIE_HTTPONLY,
        secure=AUTH_COOKIE_SECURE,
        samesite=samesite,
        domain=cookie_domain,
        path=cookie_path,
    )
    response.set_cookie(
        key=AUTH_REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=AUTH_COOKIE_HTTPONLY,
        secure=AUTH_COOKIE_SECURE,
        samesite=samesite,
        domain=cookie_domain,
        path=cookie_path,
    )


def clear_auth_cookies(response: Response) -> None:
    """Функция удаления JWT токена доступа и токена обновления из HTTP куки.

    Args:
        response: HTTP-ответ для удаления куки.
    """
    cookie_domain = AUTH_COOKIE_DOMAIN or None
    cookie_path = AUTH_COOKIE_PATH or "/"
    samesite = AUTH_COOKIE_SAMESITE

    response.delete_cookie(
        key=AUTH_ACCESS_COOKIE_NAME,
        domain=cookie_domain,
        path=cookie_path,
        secure=AUTH_COOKIE_SECURE,
        httponly=AUTH_COOKIE_HTTPONLY,
        samesite=samesite,
    )
    response.delete_cookie(
        key=AUTH_REFRESH_COOKIE_NAME,
        domain=cookie_domain,
        path=cookie_path,
        secure=AUTH_COOKIE_SECURE,
        httponly=AUTH_COOKIE_HTTPONLY,
        samesite=samesite,
    )


def set_anon_cookie(response: Response, anon_token: str) -> None:
    """Функция установки JWT токена анонимной сессии в HTTP куки.

    Args:
        response: HTTP-ответ для установки куки.
        anon_token: JWT токен анонимной сессии.
    """
    cookie_domain = AUTH_COOKIE_DOMAIN or None
    cookie_path = AUTH_COOKIE_PATH or "/"
    samesite = AUTH_COOKIE_SAMESITE

    response.set_cookie(
        key=AUTH_ANON_COOKIE_NAME,
        value=anon_token,
        max_age=JWT_ANON_TOKEN_EXPIRE_MINUTES * 60,
        httponly=AUTH_COOKIE_HTTPONLY,
        secure=AUTH_COOKIE_SECURE,
        samesite=samesite,
        domain=cookie_domain,
        path=cookie_path,
    )


def clear_anon_cookie(response: Response) -> None:
    """Функция удаления JWT токена анонимной сессии из HTTP куки.

    Args:
        response: HTTP-ответ для удаления куки.
    """
    cookie_domain = AUTH_COOKIE_DOMAIN or None
    cookie_path = AUTH_COOKIE_PATH or "/"
    samesite = AUTH_COOKIE_SAMESITE

    response.delete_cookie(
        key=AUTH_ANON_COOKIE_NAME,
        domain=cookie_domain,
        path=cookie_path,
        secure=AUTH_COOKIE_SECURE,
        httponly=AUTH_COOKIE_HTTPONLY,
        samesite=samesite,
    )


def set_oauth_state_cookie(response: Response, cookie_key: str, state: str) -> None:
    """Функция установки OAuth state в HTTP куки.

    Args:
        response: HTTP-ответ для установки куки.
        cookie_key: Имя куки (например, oauth_state_google).
        state: Значение state (CSRF token).
    """
    cookie_domain = AUTH_COOKIE_DOMAIN or None
    cookie_path = AUTH_COOKIE_PATH or "/"
    samesite = AUTH_COOKIE_SAMESITE

    response.set_cookie(
        key=cookie_key,
        value=state,
        max_age=OAUTH_STATE_COOKIE_EXPIRE_MINUTES * 60,
        httponly=AUTH_COOKIE_HTTPONLY,
        secure=AUTH_COOKIE_SECURE,
        samesite=samesite,
        domain=cookie_domain,
        path=cookie_path,
    )


def clear_oauth_state_cookie(response: Response, cookie_key: str) -> None:
    """Функция удаления OAuth state из HTTP куки.

    Args:
        response: HTTP-ответ для удаления куки.
        cookie_key: Имя куки (например, oauth_state_google).
    """
    cookie_domain = AUTH_COOKIE_DOMAIN or None
    cookie_path = AUTH_COOKIE_PATH or "/"
    samesite = AUTH_COOKIE_SAMESITE

    response.delete_cookie(
        key=cookie_key,
        domain=cookie_domain,
        path=cookie_path,
        secure=AUTH_COOKIE_SECURE,
        httponly=AUTH_COOKIE_HTTPONLY,
        samesite=samesite,
    )
