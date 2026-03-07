from typing import NoReturn
from urllib.parse import urlparse
from string import ascii_letters, digits

from email_validator import EmailNotValidError

from .constants import (
    MAX_OAUTH_CODE_LENGTH,
    MAX_OAUTH_CODE_VERIFIER_LENGTH,
    MAX_PASSWORD_LENGTH,
    MAX_OAUTH_STATE_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_OAUTH_CODE_VERIFIER_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
)
from .exceptions import (
    InvalidEmailFormatException,
    InvalidOAuthCodeFormatException,
    InvalidOAuthCodeVerifierFormatException,
    InvalidOAuthRedirectUriFormatException,
    InvalidOAuthStateFormatException,
    InvalidPasswordFormatException,
    TokenInvalidException,
    InvalidUsernameFormatException,
    InvalidVerificationCodeFormatException,
    OAuthRedirectUriMismatchException,
)
from .types import Password, RefreshToken, AccessToken
from ..types import Email, VerificationCode, Username
from ..validators import validate_email_format


OAUTH_CODE_VERIFIER_ALLOWED_CHARS = set(ascii_letters + digits + "-._~")


class AuthServiceValidators:
    """Валидаторы для auth-сервиса."""

    @classmethod
    def validate_username(cls, username: Username) -> None | NoReturn:
        """Метод валидации формата логина.

        Args:
            username: Логин пользователя для валидации.

        Raises:
            InvalidUsernameFormatException: Если username не соответствует требованиям.
        """
        if len(username) < MIN_USERNAME_LENGTH or len(username) > MAX_USERNAME_LENGTH:
            raise InvalidUsernameFormatException(
                key="auth.errors.username_length_invalid",
                fallback="Username length is invalid",
            )
        if not all(ch.islower() or ch.isdigit() or ch == "_" for ch in username):
            raise InvalidUsernameFormatException(
                key="auth.errors.username_invalid_chars",
                fallback="Username must contain only lowercase letters, numbers, and underscores",
            )
        if username.startswith("_") or username.endswith("_"):
            raise InvalidUsernameFormatException(
                key="auth.errors.username_cannot_start_or_end_with_underscore",
                fallback="Username cannot start or end with underscore",
            )

    @classmethod
    def validate_email(cls, email: Email) -> None | NoReturn:
        """Метод валидации формата email.

        Args:
            email: Email адрес пользователя для валидации.

        Raises:
            InvalidEmailFormatException: Если email имеет неверный формат или пустой.
        """
        if not email or not email.strip():
            raise InvalidEmailFormatException(
                key="auth.errors.email_cannot_be_empty",
                fallback="Email cannot be empty",
            )
        try:
            validate_email_format(email)
        except EmailNotValidError:
            raise InvalidEmailFormatException(
                key="auth.errors.invalid_email_format",
                fallback="Invalid email format",
            )

    @classmethod
    def validate_password(cls, password: Password) -> None | NoReturn:
        """Метод валидации формата пароля.

        Args:
            password: Пароль пользователя для валидации.

        Raises:
            InvalidPasswordFormatException: Если password не соответствует требованиям.
        """
        if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
            raise InvalidPasswordFormatException(
                key="auth.errors.password_length_invalid",
                fallback="Password length is invalid",
            )
        if not any(ch.isalpha() for ch in password):
            raise InvalidPasswordFormatException(
                key="auth.errors.password_must_contain_letter",
                fallback="Password must contain at least one letter",
            )
        if not any(ch.isdigit() for ch in password):
            raise InvalidPasswordFormatException(
                key="auth.errors.password_must_contain_digit",
                fallback="Password must contain at least one digit",
            )

    @classmethod
    def validate_verification_code(cls, code: VerificationCode) -> None | NoReturn:
        """Метод валидации формата кода подтверждения.

        Args:
            code: Код подтверждения.

        Raises:
            InvalidVerificationCodeFormatException: Если code не валидный.
        """
        if len(code) != 6 or not code.isdigit():
            raise InvalidVerificationCodeFormatException(
                key="auth.errors.verification_code_format_invalid",
                fallback="Verification code must be exactly 6 digits",
            )

    @classmethod
    def validate_jwt_token(cls, token: RefreshToken | AccessToken) -> None | NoReturn:
        """Метод валидации токена.

        Args:
            token: JWT токен access или refresh.

        Raises:
            TokenInvalidException: Если токен пустой.
        """
        if not token:
            raise TokenInvalidException(key="auth.errors.token_invalid", fallback="Token is invalid")

    @classmethod
    def validate_oauth_code(cls, code: str) -> None | NoReturn:
        """Метод валидации OAuth authorization code.

        Args:
            code: Authorization code.

        Raises:
            InvalidOAuthCodeFormatException: Если код пустой или превышает максимально допустимую длину.
        """
        if not code:
            raise InvalidOAuthCodeFormatException(
                key="auth.errors.oauth_code_format_invalid",
                fallback="OAuth code cannot be empty",
            )
        if len(code) > MAX_OAUTH_CODE_LENGTH:
            raise InvalidOAuthCodeFormatException(
                key="auth.errors.oauth_code_format_invalid",
                fallback="OAuth code is too long",
            )

    @classmethod
    def validate_oauth_redirect_uri(cls, redirect_uri: str) -> None | NoReturn:
        """Метод валидации OAuth redirect URI.

        Args:
            redirect_uri: Redirect URI.

        Raises:
            InvalidOAuthRedirectUriFormatException: Если URI имеет неверный формат.
        """
        parsed = urlparse(redirect_uri)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise InvalidOAuthRedirectUriFormatException(
                key="auth.errors.oauth_redirect_uri_format_invalid",
                fallback="OAuth redirect URI format is invalid",
            )

    @classmethod
    def validate_oauth_redirect_uri_matches(
        cls,
        expected_redirect_uri: str | None,
        redirect_uri: str,
    ) -> None | NoReturn:
        """Метод проверки совпадения OAuth redirect_uri с ожидаемым для провайдера.

        Args:
            expected_redirect_uri: Ожидаемый redirect_uri из конфига провайдера.
            redirect_uri: Фактический redirect_uri из запроса.

        Raises:
            OAuthRedirectUriMismatchException: Если ожидаемый задан и не совпадает с фактическим.
        """
        if not expected_redirect_uri:
            return
        if redirect_uri != expected_redirect_uri:
            raise OAuthRedirectUriMismatchException(
                key="auth.errors.oauth_redirect_uri_mismatch",
                fallback="OAuth redirect URI mismatch",
            )

    @classmethod
    def validate_oauth_code_verifier(cls, code_verifier: str | None) -> None | NoReturn:
        """Метод валидации OAuth PKCE code_verifier.

        Args:
            code_verifier: Значение PKCE code_verifier или None.

        Raises:
            InvalidOAuthCodeVerifierFormatException: Если verifier пустой, имеет
            недопустимую длину или содержит недопустимые символы.
        """
        if code_verifier is None:
            return
        if not code_verifier:
            raise InvalidOAuthCodeVerifierFormatException(
                key="auth.errors.oauth_code_verifier_format_invalid",
                fallback="OAuth code_verifier cannot be empty",
            )
        if not (MIN_OAUTH_CODE_VERIFIER_LENGTH <= len(code_verifier) <= MAX_OAUTH_CODE_VERIFIER_LENGTH):
            raise InvalidOAuthCodeVerifierFormatException(
                key="auth.errors.oauth_code_verifier_format_invalid",
                fallback="OAuth code_verifier length is invalid",
            )
        if any(ch not in OAUTH_CODE_VERIFIER_ALLOWED_CHARS for ch in code_verifier):
            raise InvalidOAuthCodeVerifierFormatException(
                key="auth.errors.oauth_code_verifier_format_invalid",
                fallback="OAuth code_verifier contains invalid characters",
            )

    @classmethod
    def validate_oauth_state(cls, state: str | None) -> None | NoReturn:
        """Метод валидации OAuth state.

        Args:
            state: Значение state.

        Raises:
            InvalidOAuthStateFormatException: Если state пустой или превышает
            максимально допустимую длину.
        """
        if state is None:
            return
        if not state:
            raise InvalidOAuthStateFormatException(
                key="auth.errors.oauth_state_format_invalid",
                fallback="OAuth state cannot be empty",
            )
        if len(state) > MAX_OAUTH_STATE_LENGTH:
            raise InvalidOAuthStateFormatException(
                key="auth.errors.oauth_state_format_invalid",
                fallback="OAuth state is too long",
            )
