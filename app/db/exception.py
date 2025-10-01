from .types import ExceptionMessage
from ..common.common import FormException, StringEnum


class DatabaseManagerException(FormException):
    """Базовое исключение для всех ошибок, возникающих в процессе работы менеджера базы данных."""


class DatabaseManagerMessages(StringEnum):
    """Перечисление сообщений об ошибках, используемых менеджером базы данных."""

    INVALID_URL_TYPE_ERROR: ExceptionMessage = "Database URL must be a string!"
    EMPTY_URL_ERROR: ExceptionMessage = "Database URL must not be empty!"
    MISSING_SCHEME_ERROR: ExceptionMessage = "Database URL must contain a scheme (e.g., 'postgresql://')!"
    UNSUPPORTED_SCHEME_ERROR: ExceptionMessage = (
        "Unsupported database scheme '{scheme}'. Supported schemes: {supported}!"
    )
    INVALID_SQLITE_FORMAT_ERROR: ExceptionMessage = "Invalid SQLite URL format!"
    ENGINE_CREATION_FAILED_ERROR: ExceptionMessage = "Failed to initialize database engine: {error}!"
    INVALID_ENGINE_CONFIG_ERROR: ExceptionMessage = "Invalid database configuration: {error}!"
    SESSION_ERROR: ExceptionMessage = "Database session error: {error}!"
    UNEXPECTED_SESSION_ERROR: ExceptionMessage = "Unexpected session error: {error}!"
    ROLLBACK_FAILED_ERROR: ExceptionMessage = "Failed to rollback session: {error}!"
    CLOSE_FAILED_ERROR: ExceptionMessage = "Failed to close session gracefully: {error}!"
