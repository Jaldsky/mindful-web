import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.localizer import localize_key
from ..core.common import path_matches
from ..exceptions import AppException
from .routes import (
    ANALYTICS_USAGE_PATH,
    ANALYTICS_SUMMARY_PATH,
    ANALYTICS_TIMELINE_PATH,
    HEALTHCHECK_PATH,
    SEND_EVENTS_PATH,
    AUTH_LOGIN_PATH,
    AUTH_REFRESH_PATH,
    AUTH_REGISTER_PATH,
    AUTH_RESEND_CODE_PATH,
    AUTH_VERIFY_PATH,
    AUTH_LOGOUT_PATH,
    AUTH_ANONYMOUS_PATH,
    AUTH_SESSION_PATH,
    AUTH_OAUTH_CALLBACK_PATH,
    AUTH_OAUTH_AUTHORIZE_PATH,
    USER_PROFILE_PATH,
    USER_PROFILE_USERNAME_PATH,
    USER_PROFILE_EMAIL_PATH,
)
from ..schemas import ErrorCode, ErrorDetailData
from ..schemas.general import UnprocessableEntitySchema, InternalServerErrorSchema, BadRequestSchema
from ..schemas.general.service_unavailable_schema import ServiceUnavailableSchema
from ..services.auth.cookies import clear_auth_cookies
from ..services.auth.exceptions import TokenExpiredException, TokenInvalidException

logger = logging.getLogger(__name__)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик необработанных исключений.

    Args:
        request: Объект входящего HTTP-запроса.
        exc: Необработанное исключение Exception.

    Returns:
        JSONResponse со статусом 500 и телом InternalServerErrorSchema.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_schema = InternalServerErrorSchema(
        code=ErrorCode.INTERNAL_ERROR,
        message="Internal server error",
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_schema.model_dump(mode="json"),
    )


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Универсальный обработчик для всех AppException.

    Args:
        request: Объект входящего HTTP-запроса.
        exc: Исключение приложения AppException.

    Returns:
        JSONResponse со статусом и телом из exc или 500 при неверном типе.
    """
    if not isinstance(exc, AppException):
        error_schema = InternalServerErrorSchema(
            code=ErrorCode.INTERNAL_ERROR, message="Unknown exception type handled by app_exception_handler"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_schema.model_dump(mode="json"),
        )

    if exc.status_code >= 500:
        logger.error(f"App error: {exc.fallback}", exc_info=True)
    else:
        logger.warning(f"App warning: {exc.fallback}")

    content = exc.get_response_content()
    i18n_key = getattr(exc, "key", None)
    if i18n_key:
        params = getattr(exc, "translation_params", None) or {}
        translated_message = localize_key(
            request, i18n_key, content["message"], **{k: str(v) for k, v in params.items()}
        )
        if isinstance(translated_message, str):
            content["message"] = translated_message
            for detail in content.get("details") or []:
                if isinstance(detail, dict) and "message" in detail:
                    detail["message"] = translated_message

    response = JSONResponse(status_code=exc.status_code, content=content)
    if isinstance(exc, (TokenExpiredException, TokenInvalidException)):
        clear_auth_cookies(response)
    return response


async def bad_request_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 400 Bad Request.

    Args:
        request: Объект входящего HTTP-запроса.
        exc: Ошибка валидации запроса RequestValidationError.

    Returns:
        JSONResponse со статусом 400 и телом BadRequestSchema с деталями валидации.
    """
    error_details = None
    if isinstance(exc, RequestValidationError):
        error_details = [
            ErrorDetailData(
                field=".".join(str(loc) for loc in err.get("loc", ())),
                message=localize_key(
                    request,
                    f"validation.{err.get('type', '')}",
                    err.get("msg", ""),
                    **{k: str(v) for k, v in (err.get("ctx") or {}).items()},
                ),
                value=err.get("input"),
            )
            for err in exc.errors()
        ] or None

    message = localize_key(request, "validation.payload_validation_failed", "Payload validation failed")

    error_schema = BadRequestSchema(code=ErrorCode.VALIDATION_ERROR, message=message, details=error_details)

    logger.warning(f"Validation error: {error_schema.message}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_schema.model_dump(mode="json"),
    )


async def method_not_allowed_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 405 Method Not Allowed.

    Args:
        request: Объект входящего HTTP-запроса.
        exc: Исключение.

    Returns:
        JSONResponse со статусом 405 и схемой ошибки.
    """
    from ..services.healthcheck import healthcheck_method_not_allowed_response
    from ..services.events.http_handler import save_events_method_not_allowed_response
    from ..services.analytics.http_handler import (
        analytics_usage_method_not_allowed_response,
        analytics_summary_method_not_allowed_response,
        analytics_timeline_method_not_allowed_response,
    )
    from ..services.auth.http_handler import (
        auth_login_method_not_allowed_response,
        auth_logout_method_not_allowed_response,
        auth_refresh_method_not_allowed_response,
        auth_register_method_not_allowed_response,
        auth_resend_code_method_not_allowed_response,
        auth_verify_method_not_allowed_response,
        auth_anonymous_method_not_allowed_response,
        auth_session_method_not_allowed_response,
        auth_oauth_callback_method_not_allowed_response,
        auth_oauth_authorize_method_not_allowed_response,
    )
    from ..services.user.http_handler import (
        user_profile_method_not_allowed_response,
        user_profile_username_method_not_allowed_response,
        user_profile_email_method_not_allowed_response,
    )

    if str(request.url.path) == HEALTHCHECK_PATH:
        return healthcheck_method_not_allowed_response(request)

    if str(request.url.path) == SEND_EVENTS_PATH:
        return save_events_method_not_allowed_response(request)

    if str(request.url.path) == ANALYTICS_USAGE_PATH:
        return analytics_usage_method_not_allowed_response(request)

    if str(request.url.path) == ANALYTICS_SUMMARY_PATH:
        return analytics_summary_method_not_allowed_response(request)

    if str(request.url.path) == ANALYTICS_TIMELINE_PATH:
        return analytics_timeline_method_not_allowed_response(request)

    if str(request.url.path) == AUTH_REGISTER_PATH:
        return auth_register_method_not_allowed_response(request)

    if str(request.url.path) == AUTH_LOGIN_PATH:
        return auth_login_method_not_allowed_response(request)

    if str(request.url.path) == AUTH_REFRESH_PATH:
        return auth_refresh_method_not_allowed_response(request)

    if str(request.url.path) == AUTH_VERIFY_PATH:
        return auth_verify_method_not_allowed_response(request)

    if str(request.url.path) == AUTH_RESEND_CODE_PATH:
        return auth_resend_code_method_not_allowed_response(request)

    if str(request.url.path) == AUTH_LOGOUT_PATH:
        return auth_logout_method_not_allowed_response(request)

    if str(request.url.path) == AUTH_ANONYMOUS_PATH:
        return auth_anonymous_method_not_allowed_response(request)

    if str(request.url.path) == AUTH_SESSION_PATH:
        return auth_session_method_not_allowed_response(request)

    if path_matches(str(request.url.path), AUTH_OAUTH_CALLBACK_PATH):
        return auth_oauth_callback_method_not_allowed_response(request)

    if path_matches(str(request.url.path), AUTH_OAUTH_AUTHORIZE_PATH):
        return auth_oauth_authorize_method_not_allowed_response(request)

    if str(request.url.path) == USER_PROFILE_PATH:
        return user_profile_method_not_allowed_response(request)

    if str(request.url.path) == USER_PROFILE_USERNAME_PATH:
        return user_profile_username_method_not_allowed_response(request)

    if str(request.url.path) == USER_PROFILE_EMAIL_PATH:
        return user_profile_email_method_not_allowed_response(request)

    if isinstance(exc, StarletteHTTPException) and exc.detail:
        logger.warning(f"Method not allowed: {exc.detail}")

    detail = localize_key(request, "general.method_not_allowed", "Method not allowed")

    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content={"detail": detail},
    )


async def unprocessable_entity_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 422 Unprocessable Entity.

    Args:
        request: Объект входящего HTTP-запроса.
        exc: Исключение с кодом 422.

    Returns:
        JSONResponse со статусом 422 и телом UnprocessableEntitySchema.
    """
    _UNPROCESSABLE_ENTITY_DEFAULT_KEY = "general.business_validation_failed"
    _UNPROCESSABLE_ENTITY_DEFAULT_FALLBACK = "Business validation failed"

    message_key = _UNPROCESSABLE_ENTITY_DEFAULT_KEY
    if isinstance(exc, StarletteHTTPException) and exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        if isinstance(exc.detail, str) and exc.detail:
            message_key = exc.detail
        elif isinstance(exc.detail, dict):
            logger.warning(f"Unprocessable entity (dict detail): {exc.detail}")

    fallback = (
        _UNPROCESSABLE_ENTITY_DEFAULT_FALLBACK if message_key == _UNPROCESSABLE_ENTITY_DEFAULT_KEY else message_key
    )
    message = localize_key(request, message_key, fallback)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=UnprocessableEntitySchema(
            code=ErrorCode.BUSINESS_VALIDATION_ERROR,
            message=message,
            details=None,
        ).model_dump(mode="json"),
    )


async def internal_server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 500 Internal Server Error.

    Args:
        request: Объект входящего HTTP-запроса.
        exc: Исключение.

    Returns:
        JSONResponse со статусом 500 и телом InternalServerErrorSchema.
    """
    from sqlalchemy.exc import ArgumentError, SQLAlchemyError
    from ..db.exceptions import DatabaseManagerException

    message = "Internal server error"
    error_code = ErrorCode.INTERNAL_ERROR

    if isinstance(exc, (DatabaseManagerException, ArgumentError, SQLAlchemyError)):
        error_code = ErrorCode.DATABASE_ERROR
        message = "Database error"

    logger.error(f"Internal server error: {exc}", exc_info=True)

    error_schema = InternalServerErrorSchema(
        code=error_code,
        message=message,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_schema.model_dump(mode="json"),
    )


async def service_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 503 Service Unavailable.

    Args:
        request: Объект входящего HTTP-запроса.
        exc: Исключение.

    Returns:
        JSONResponse со статусом 503 и телом ServiceUnavailableSchema.
    """
    message = "Service is not available"
    if isinstance(exc, StarletteHTTPException) and exc.detail:
        logger.error(f"Service unavailable: {exc.detail}", exc_info=True)

    error_schema = ServiceUnavailableSchema(
        code=ErrorCode.SERVICE_UNAVAILABLE,
        message=message,
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_schema.model_dump(mode="json"),
    )
