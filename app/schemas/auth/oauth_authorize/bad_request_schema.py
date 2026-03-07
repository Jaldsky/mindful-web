from typing import Union

from pydantic import Field

from ...error_response_schema import ErrorCode, ErrorResponseSchema
from ..auth_error_code import AuthErrorCode


class OAuthAuthorizeBadRequestSchema(ErrorResponseSchema):
    """Схема ошибки 400 Bad Request для OAuth authorize endpoint (например, неподдерживаемый провайдер)."""

    code: Union[ErrorCode, AuthErrorCode] = Field(..., description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "OAUTH_PROVIDER_UNSUPPORTED",
                "message": "OAuth provider is not supported",
                "details": None,
                "meta": {
                    "request_id": "5d4c75de-7d7d-4f2d-a86f-4d6d00d2d2f7",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
