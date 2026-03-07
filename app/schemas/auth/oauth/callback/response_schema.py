from pydantic import BaseModel, Field


class OAuthCallbackResponseSchema(BaseModel):
    """Схема ответа на OAuth callback."""

    code: str = Field(default="OK", description="Код ответа")
    message: str = Field(..., description="Сообщение")
    access_token: str = Field(..., description="Access токен")
    refresh_token: str = Field(..., description="Refresh токен")
