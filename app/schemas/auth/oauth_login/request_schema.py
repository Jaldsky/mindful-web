from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic.types import StrictStr


class OAuthLoginRequestSchema(BaseModel):
    """Схема запроса авторизации через OAuth провайдера."""

    code: StrictStr = Field(..., description="Authorization code от OAuth провайдера")
    redirect_uri: StrictStr = Field(..., description="Redirect URI, использованный во время OAuth")
    code_verifier: StrictStr | None = Field(None, description="PKCE code_verifier (если использовался)")
    state: StrictStr | None = Field(None, description="State, полученный от OAuth провайдера")

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, v: Any) -> Any:
        if not isinstance(v, str):
            return v
        from ....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_oauth_code(v)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        from ....services.auth.validators import AuthServiceValidators

        AuthServiceValidators.validate_oauth_code(v)
        return v

    @field_validator("redirect_uri", mode="before")
    @classmethod
    def normalize_redirect_uri(cls, v: Any) -> Any:
        if not isinstance(v, str):
            return v
        from ....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_oauth_redirect_uri(v)

    @field_validator("redirect_uri")
    @classmethod
    def validate_redirect_uri(cls, v: str) -> str:
        from ....services.auth.validators import AuthServiceValidators

        AuthServiceValidators.validate_oauth_redirect_uri(v)
        return v

    @field_validator("code_verifier", mode="before")
    @classmethod
    def normalize_code_verifier(cls, v: Any) -> Any:
        if v is None:
            return None
        if not isinstance(v, str):
            return v
        from ....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_oauth_code_verifier(v)

    @field_validator("code_verifier")
    @classmethod
    def validate_code_verifier(cls, v: str | None) -> str | None:
        from ....services.auth.validators import AuthServiceValidators

        AuthServiceValidators.validate_oauth_code_verifier(v)
        return v

    @field_validator("state", mode="before")
    @classmethod
    def normalize_state(cls, v: Any) -> Any:
        if v is None:
            return None
        if not isinstance(v, str):
            return v
        from ....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_oauth_state(v)

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str | None) -> str | None:
        from ....services.auth.validators import AuthServiceValidators

        AuthServiceValidators.validate_oauth_state(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "code": "4/0AbCdEfGhIjKlMn",
                "redirect_uri": "http://localhost:8000/api/v1/auth/oauth/google/callback",
                "code_verifier": "s256-code-verifier-value",
                "state": "oauth-state-value",
            }
        }
