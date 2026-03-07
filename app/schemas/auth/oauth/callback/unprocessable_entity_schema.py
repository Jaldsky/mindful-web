from typing import Union

from pydantic import Field

from ....error_response_schema import ErrorCode, ErrorResponseSchema
from ...auth_error_code import AuthErrorCode


class OAuthCallbackUnprocessableEntitySchema(ErrorResponseSchema):
    """Схема ошибки 422 Unprocessable Entity для OAuth callback endpoint."""

    code: Union[ErrorCode, AuthErrorCode] = Field(..., description="Код ошибки")
