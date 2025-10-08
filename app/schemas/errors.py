from pydantic import BaseModel, Field

from ..common.common import StringEnum


class ErrorCode(StringEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_USER_ID = "INVALID_USER_ID"
    TIMESTAMP_ERROR = "TIMESTAMP_ERROR"

    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CONFLICT = "CONFLICT"


class CommonErrorSchema(BaseModel):
    code: ErrorCode = Field(..., examples=[ErrorCode.VALIDATION_ERROR])
    message: str = Field(..., examples=["Invalid domain format"])
