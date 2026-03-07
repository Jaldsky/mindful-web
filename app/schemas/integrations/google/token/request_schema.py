from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic.types import StrictStr


class GoogleOAuthTokenRequestBodySchema(BaseModel):
    """Тело запроса POST token."""

    code: StrictStr = Field(..., description="Authorization code от Google")
    client_id: StrictStr = Field(..., description="Client ID приложения")
    client_secret: StrictStr = Field(..., description="Client secret приложения")
    redirect_uri: StrictStr = Field(..., description="Redirect URI, использованный при запросе кода")
    grant_type: Literal["authorization_code"] = Field(
        "authorization_code",
        description="Тип grant (OAuth 2.0 authorization code)",
    )
    code_verifier: StrictStr | None = Field(None, description="PKCE code_verifier (если использовался)")

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, v: Any) -> Any:
        if not isinstance(v, str):
            return v
        from .....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_oauth_code(v)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        from .....services.auth.validators import AuthServiceValidators

        AuthServiceValidators.validate_oauth_code(v)
        return v

    @field_validator("redirect_uri", mode="before")
    @classmethod
    def normalize_redirect_uri(cls, v: Any) -> Any:
        if not isinstance(v, str):
            return v
        from .....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_oauth_redirect_uri(v)

    @field_validator("redirect_uri")
    @classmethod
    def validate_redirect_uri(cls, v: str) -> str:
        from .....services.auth.validators import AuthServiceValidators

        AuthServiceValidators.validate_oauth_redirect_uri(v)
        return v

    @field_validator("code_verifier", mode="before")
    @classmethod
    def normalize_code_verifier(cls, v: Any) -> Any:
        if v is None:
            return None
        if not isinstance(v, str):
            return v
        from .....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_oauth_code_verifier(v)

    @field_validator("code_verifier")
    @classmethod
    def validate_code_verifier(cls, v: str | None) -> str | None:
        from .....services.auth.validators import AuthServiceValidators

        AuthServiceValidators.validate_oauth_code_verifier(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "code": "4/0AbCdEfGhIjKlMn",
                "client_id": "123456789-xxx.apps.googleusercontent.com",
                "client_secret": "GOCSPX-xxx",
                "redirect_uri": "http://localhost:8000/api/v1/auth/oauth/google/callback",
                "grant_type": "authorization_code",
                "code_verifier": "s256-code-verifier-value",
            }
        }
