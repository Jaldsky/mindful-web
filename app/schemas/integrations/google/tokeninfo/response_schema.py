from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic.types import StrictStr


class GoogleOAuthTokenInfoResponseSchema(BaseModel):
    """Ответ Google tokeninfo."""

    sub: StrictStr = Field(..., description="Уникальный идентификатор пользователя у провайдера")
    email: StrictStr | None = Field(None, description="Email пользователя")
    email_verified: bool = Field(False, description="Флаг подтверждения email")
    iss: StrictStr = Field(..., description="Issuer токена")
    aud: StrictStr = Field(..., description="Audience (client_id)")
    name: StrictStr | None = Field(None, description="Отображаемое имя")
    picture: StrictStr | None = Field(None, description="URL аватара")
    given_name: StrictStr | None = Field(None, description="Имя")
    family_name: StrictStr | None = Field(None, description="Фамилия")

    @field_validator("email_verified", mode="before")
    @classmethod
    def normalize_email_verified(cls, v: Any) -> bool:
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "yes")
        return bool(v)

    class Config:
        json_schema_extra = {
            "example": {
                "sub": "108234567890123456789",
                "email": "user@gmail.com",
                "email_verified": True,
                "iss": "https://accounts.google.com",
                "aud": "123456789-xxx.apps.googleusercontent.com",
                "name": "John Doe",
                "picture": "https://lh3.googleusercontent.com/...",
            }
        }
