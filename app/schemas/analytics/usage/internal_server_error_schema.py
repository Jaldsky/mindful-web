from typing import Union
from pydantic import Field

from ...error_response_schema import ErrorCode
from ..analytics_error_code import AnalyticsErrorCode
from ...general import InternalServerErrorSchema


class AnalyticsDomainsInternalServerErrorSchema(InternalServerErrorSchema):
    """Схема ошибки 500 Internal Server Error для доменного analytics endpoint."""

    code: Union[ErrorCode | AnalyticsErrorCode] = Field(..., description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "UNEXPECTED_ERROR",
                "message": "An unexpected error occurred while processing usage analytics!",
                "details": None,
                "meta": {
                    "request_id": "aaa5c2b3-1a1b-4612-8ad9-e9e731ea82c0",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
