"""Схема path-параметра provider для OAuth эндпоинтов (authorize и callback)."""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from ....services.auth.normalizers import AuthServiceNormalizers
from ....services.auth.validators import AuthServiceValidators


class OAuthProviderPathSchema(BaseModel):
    """Path-параметр provider с нормализацией и валидацией."""

    provider: str = Field(..., description="Имя OAuth-провайдера (например, google)")

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(cls, v: Any) -> str:
        """Нормализация: приведение к строке и strip/lower."""
        if not isinstance(v, str):
            raise ValueError("provider must be a string")
        return AuthServiceNormalizers.normalize_oauth_provider(v)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Валидация: не пустое значение после нормализации.

        Raises:
            InvalidOAuthProviderFormatException: Если provider пустой (422).
        """
        AuthServiceValidators.validate_oauth_provider(v)
        return v
