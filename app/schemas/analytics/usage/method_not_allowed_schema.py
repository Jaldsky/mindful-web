from ...error_response_schema import ErrorResponseSchema


class AnalyticsDomainsMethodNotAllowedSchema(ErrorResponseSchema):
    """Схема ошибки 405 Method Not Allowed для доменного analytics endpoint."""

    class Config:
        json_schema_extra = {
            "example": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "Method not allowed. Only GET method is supported for this endpoint.",
                "details": None,
                "meta": {
                    "request_id": "aaa5c2b3-1a1b-4612-8ad9-e9e731ea82c0",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
