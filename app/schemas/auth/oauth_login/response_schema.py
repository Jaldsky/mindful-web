from pydantic import BaseModel, Field


class OAuthLoginResponseSchema(BaseModel):
    """Схема ответа на OAuth авторизацию."""

    code: str = Field(default="OK", description="Код ответа")
    message: str = Field(..., description="Сообщение")
    access_token: str = Field(..., description="Access токен")
    refresh_token: str = Field(..., description="Refresh токен")
