from ...db.types import ExceptionMessage
from ...common.common import FormException, StringEnum


class EventsServiceException(FormException):
    """Базовое исключение приложения."""


class EventsServiceMessages(StringEnum):
    """Перечисление сообщений об ошибках."""

    GET_OR_CREATE_USER_ERROR: ExceptionMessage = "Unable to create/find user {user_id}!"
    ADD_EVENTS_ERROR: ExceptionMessage = "Failed to insert event into the events table!"
    DATA_INTEGRITY_ERROR: ExceptionMessage = "Data integrity issue when saving events!"
    DATA_SAVE_ERROR: ExceptionMessage = "Database error while saving events!"
    UNEXPECTED_ERROR = "An unexpected error occurred while processing events!"
