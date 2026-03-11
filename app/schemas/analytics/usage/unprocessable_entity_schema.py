from typing import Union
from pydantic import Field

from ...error_response_schema import ErrorResponseSchema, ErrorCode
from ..analytics_error_code import AnalyticsErrorCode


class AnalyticsDomainsUnprocessableEntitySchema(ErrorResponseSchema):
    """Схема ошибки 422 Unprocessable Entity для доменного analytics endpoint."""

    code: Union[ErrorCode | AnalyticsErrorCode] = Field(..., description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "INVALID_DATE_FORMAT",
                "message": "Invalid date format",
                "details": [
                    {
                        "field": "from",
                        "message": "Invalid date format",
                        "value": None,
                    }
                ],
                "meta": {
                    "request_id": "5d4c75de-7d7d-4f2d-a86f-4d6d00d2d2f7",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
