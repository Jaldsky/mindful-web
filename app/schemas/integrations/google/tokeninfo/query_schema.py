from pydantic import BaseModel, Field, field_validator
from pydantic.types import StrictStr


class GoogleOAuthTokenInfoQuerySchema(BaseModel):
    """Query-параметры запроса GET tokeninfo."""

    id_token: StrictStr = Field(..., description="JWT id_token от Google")

    @field_validator("id_token")
    @classmethod
    def validate_id_token_non_empty(cls, v: str) -> str:
        if not (v and v.strip()):
            from .....services.auth.exceptions import OAuthCodeExchangeFailedException

            raise OAuthCodeExchangeFailedException(
                key="auth.errors.oauth_code_exchange_failed",
                fallback="id_token is required",
            )
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "id_token": "eyJhbGciOiJSUzI1NiIs...",
            }
        }
