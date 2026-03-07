from pydantic import BaseModel, Field
from pydantic.types import StrictStr


class GoogleOAuthTokenResponseSchema(BaseModel):
    """Ответ эндпоинта token."""

    id_token: StrictStr = Field(..., description="JWT id_token от Google")
    access_token: StrictStr | None = Field(None, description="Access token")
    refresh_token: StrictStr | None = Field(None, description="Refresh token")
    expires_in: int | None = Field(None, description="Время жизни access_token в секундах")
    token_type: StrictStr | None = Field(None, description="Тип токена (например, Bearer)")

    class Config:
        json_schema_extra = {
            "example": {
                "id_token": "eyJhbGciOiJSUzI1NiIs...",
                "access_token": "ya29.a0AfH6SMBx...",
                "refresh_token": "1//0gXXX...",
                "expires_in": 3599,
                "token_type": "Bearer",
            }
        }
