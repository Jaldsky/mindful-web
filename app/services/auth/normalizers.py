from typing import Any

from .types import Password, AccessToken, RefreshToken
from .constants import AUTH_OAUTH_STATE_COOKIE_NAME
from ..types import Email, Username
from ..normalizers import normalize_email


class AuthServiceNormalizers:
    """Класс с нормализаторами для auth-сервиса."""

    @staticmethod
    def normalize_username(username: Username) -> Username:
        """Метод нормализации логина.

        Args:
            username: Логин пользователя.

        Returns:
            Нормализованный логин.
        """
        return (username or "").strip().lower()

    @staticmethod
    def normalize_email(email: Email) -> Email:
        """Метод нормализации email.

        Args:
            email: Email адрес пользователя.

        Returns:
            Нормализованный email адрес.
        """
        return normalize_email(email)

    @staticmethod
    def normalize_password(password: Password) -> Password:
        """Метод нормализации пароля.

        Args:
            password: Пароль пользователя.

        Returns:
            Пароль или пустая строка, если None.
        """
        return password or ""

    @staticmethod
    def normalize_jwt_token(token: RefreshToken | AccessToken) -> RefreshToken | AccessToken:
        """Метод нормализации JWT токена.

        Args:
            token: JWT токен access или refresh.

        Returns:
            Нормализованный токен.
        """
        return (token or "").strip()

    @staticmethod
    def normalize_oauth_provider(provider: str) -> str:
        """Метод нормализации имени OAuth-провайдера.

        Args:
            provider: Имя OAuth-провайдера.

        Returns:
            Нормализованное имя провайдера.
        """
        return (provider or "").strip().lower()

    @staticmethod
    def normalize_email_verified_flag(value: Any) -> bool:
        """Метод нормализации флага подтверждения электронной почты.

        Args:
            value: Значение флага электронной почты.

        Returns:
            Нормализованный флаг электронной почты.
        """
        if isinstance(value, bool):
            return value
        return str(value).lower() == "true"

    @staticmethod
    def normalize_oauth_state_cookie_name(provider: str) -> str:
        """Метод нормализации имени cookie для state выбранного OAuth-провайдера.

        Args:
            provider: Имя OAuth-провайдера.

        Returns:
            Нормализованное имя OAuth-провайдера.
        """
        normalized = (provider or "").strip().lower()
        return f"{AUTH_OAUTH_STATE_COOKIE_NAME}_{normalized}"

    @staticmethod
    def normalize_oauth_code(code: str) -> str:
        """Метод нормализации OAuth authorization code.

        Args:
            code: Значение authorization code от OAuth-провайдера.

        Returns:
            Нормализованный authorization code.
        """
        return (code or "").strip()

    @staticmethod
    def normalize_oauth_redirect_uri(redirect_uri: str) -> str:
        """Метод нормализации OAuth redirect URI.

        Args:
            redirect_uri: Redirect URI, использованный при OAuth-авторизации.

        Returns:
            Нормализованный redirect URI.
        """
        return (redirect_uri or "").strip()

    @staticmethod
    def normalize_oauth_code_verifier(code_verifier: str | None) -> str | None:
        """Метод нормализации OAuth PKCE code_verifier.

        Args:
            code_verifier: Значение PKCE code_verifier или None.

        Returns:
            Нормализованный code_verifier.
        """
        if code_verifier is None:
            return None
        return code_verifier.strip()

    @staticmethod
    def normalize_oauth_state(state: str | None) -> str | None:
        """Метод нормализации OAuth state.

        Args:
            state: Значение state из OAuth-redirect или None.

        Returns:
            Нормализованный state.
        """
        if state is not None:
            return state.strip()
