from ..exceptions import (
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    UnprocessableEntityException,
    InternalServerErrorException,
)
from ...schemas.auth.auth_error_code import AuthErrorCode


# Исключения для 400
class OAuthProviderUnsupportedException(BadRequestException):
    """Неподдерживаемый OAuth провайдер (400)."""

    error_code = AuthErrorCode.OAUTH_PROVIDER_UNSUPPORTED


class OAuthRedirectUriMismatchException(BadRequestException):
    """Передан неподходящий redirect_uri для OAuth (400)."""

    error_code = AuthErrorCode.OAUTH_REDIRECT_URI_MISMATCH


# Исключения для 401
class TokenInvalidException(UnauthorizedException):
    """Невалидный токен (401)."""

    error_code = AuthErrorCode.TOKEN_INVALID


class TokenExpiredException(UnauthorizedException):
    """Истёкший токен (401)."""

    error_code = AuthErrorCode.TOKEN_EXPIRED


class TokenMissingException(UnauthorizedException):
    """Отсутствующий токен (401)."""

    error_code = AuthErrorCode.TOKEN_MISSING


class InvalidCredentialsException(UnauthorizedException):
    """Неверные учетные данные (401)."""

    error_code = AuthErrorCode.INVALID_CREDENTIALS


class UserNotFoundException(UnauthorizedException):
    """Пользователь не найден в системе (401)."""

    error_code = AuthErrorCode.USER_NOT_FOUND


class OAuthCodeExchangeFailedException(UnauthorizedException):
    """Не удалось обменять код OAuth на токены (401)."""

    error_code = AuthErrorCode.OAUTH_CODE_EXCHANGE_FAILED


class OAuthStateInvalidException(UnauthorizedException):
    """State OAuth невалиден или отсутствует (401)."""

    error_code = AuthErrorCode.OAUTH_STATE_INVALID


# Исключения для 403
class EmailNotVerifiedException(ForbiddenException):
    """Email не подтверждён (403)."""

    error_code = AuthErrorCode.EMAIL_NOT_VERIFIED


# Исключения для 409
class EmailAlreadyExistsException(ConflictException):
    """Email уже используется (409)."""

    error_code = AuthErrorCode.EMAIL_ALREADY_EXISTS


class UsernameAlreadyExistsException(ConflictException):
    """Логин уже занят (409)."""

    error_code = AuthErrorCode.USERNAME_ALREADY_EXISTS


# Исключения для 422
class InvalidUsernameFormatException(UnprocessableEntityException):
    """Неверный формат логина (422)."""

    error_code = AuthErrorCode.INVALID_USERNAME_FORMAT


class InvalidEmailFormatException(UnprocessableEntityException):
    """Неверный формат email (422)."""

    error_code = AuthErrorCode.INVALID_EMAIL_FORMAT


class InvalidPasswordFormatException(UnprocessableEntityException):
    """Неверный формат пароля (422)."""

    error_code = AuthErrorCode.INVALID_PASSWORD_FORMAT


class EmailAlreadyVerifiedException(UnprocessableEntityException):
    """Email уже подтверждён (422)."""

    error_code = AuthErrorCode.EMAIL_ALREADY_VERIFIED


class TooManyAttemptsException(UnprocessableEntityException):
    """Слишком много попыток (422)."""

    error_code = AuthErrorCode.TOO_MANY_ATTEMPTS


class OAuthEmailMissingException(UnprocessableEntityException):
    """Провайдер не вернул email (422)."""

    error_code = AuthErrorCode.OAUTH_EMAIL_MISSING


class OAuthEmailNotVerifiedException(UnprocessableEntityException):
    """Email у OAuth провайдера не подтвержден (422)."""

    error_code = AuthErrorCode.OAUTH_EMAIL_NOT_VERIFIED


class InvalidVerificationCodeFormatException(UnprocessableEntityException):
    """Неверный формат кода подтверждения (422)."""

    error_code = AuthErrorCode.INVALID_VERIFICATION_CODE


class InvalidOAuthCodeFormatException(UnprocessableEntityException):
    """Неверный формат OAuth authorization code (422)."""

    error_code = AuthErrorCode.INVALID_OAUTH_CODE_FORMAT


class InvalidOAuthRedirectUriFormatException(UnprocessableEntityException):
    """Неверный формат OAuth redirect URI (422)."""

    error_code = AuthErrorCode.INVALID_OAUTH_REDIRECT_URI_FORMAT


class InvalidOAuthStateFormatException(UnprocessableEntityException):
    """Неверный формат OAuth state (422)."""

    error_code = AuthErrorCode.INVALID_OAUTH_STATE_FORMAT


class InvalidOAuthCodeVerifierFormatException(UnprocessableEntityException):
    """Неверный формат OAuth PKCE code_verifier (422)."""

    error_code = AuthErrorCode.INVALID_OAUTH_CODE_VERIFIER_FORMAT


class VerificationCodeExpiredException(UnprocessableEntityException):
    """Код подтверждения истёк (422)."""

    error_code = AuthErrorCode.VERIFICATION_CODE_EXPIRED


class VerificationCodeInvalidException(UnprocessableEntityException):
    """Код подтверждения неверный (422)."""

    error_code = AuthErrorCode.VERIFICATION_CODE_INVALID


# Исключения для 500
class AuthServiceException(InternalServerErrorException):
    """Ошибка сервиса авторизации (500)."""

    error_code = AuthErrorCode.AUTH_SERVICE_ERROR


class EmailSendFailedException(InternalServerErrorException):
    """Ошибка сервиса email (500)."""

    error_code = AuthErrorCode.EMAIL_SEND_FAILED
