from typing import Literal

from pydantic import BaseModel, Field


class OAuthAuthorizeQueryParamsSchema(BaseModel):
    """Схема query-параметров для OAuth authorization URL."""

    client_id: str = Field(..., description="Client ID приложения у провайдера")
    redirect_uri: str = Field(..., description="Redirect URI после авторизации")
    response_type: Literal["code"] = Field("code", description="OAuth2 response_type")
    scope: str = Field(..., description="Запрашиваемые scope")
    state: str = Field(..., description="CSRF state token")
    access_type: Literal["offline"] = Field("offline", description="Запрос refresh token (Google)")
    include_granted_scopes: Literal["true"] = Field("true", description="Включить ранее выданные scope (Google)")
    prompt: Literal["consent"] = Field("consent", description="Показывать экран согласия (Google)")
