from typing import Union

from pydantic import Field

from ...error_response_schema import ErrorCode, ErrorResponseSchema
from ..auth_error_code import AuthErrorCode


class OAuthLoginUnauthorizedSchema(ErrorResponseSchema):
    """Схема ошибки 401 Unauthorized для OAuth login endpoint."""

    code: Union[ErrorCode, AuthErrorCode] = Field(..., description="Код ошибки")
