from typing import Union

from pydantic import Field

from ....error_response_schema import ErrorCode, ErrorResponseSchema
from ...auth_error_code import AuthErrorCode


class OAuthCallbackBadRequestSchema(ErrorResponseSchema):
    """Схема ошибки 400 Bad Request для OAuth callback endpoint."""

    code: Union[ErrorCode, AuthErrorCode] = Field(..., description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "BAD_REQUEST",
                "message": "Validation error",
                "details": [
                    {
                        "field": "redirect_uri",
                        "message": "OAuth redirect URI mismatch",
                        "value": "http://localhost:5173/oauth/google/callback",
                    }
                ],
                "meta": {
                    "request_id": "5d4c75de-7d7d-4f2d-a86f-4d6d00d2d2f7",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
