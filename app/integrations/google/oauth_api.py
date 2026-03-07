from typing import Any, NoReturn

from ...services.auth.config import OAuthProviderConfig
from ...core.request import AsyncRequestBase
from ...schemas.integrations.google import (
    GoogleOAuthTokenRequestBodySchema,
    GoogleOAuthTokenResponseSchema,
    GoogleOAuthTokenInfoQuerySchema,
    GoogleOAuthTokenInfoResponseSchema,
)


class GoogleOAuthApiBase(AsyncRequestBase):
    """Базовый клиент для запросов к Google OAuth API."""

    def __init__(self, timeout: float = 10.0, **kwargs: Any) -> None:
        """Инициализация базового клиента.

        Args:
            timeout: Таймаут HTTP-запросов в секундах.
            **kwargs: Дополнительные аргументы для AsyncRequestBase.
        """
        super().__init__(
            base_url="",
            timeout=timeout,
            **kwargs,
        )


class GoogleOAuthApi(GoogleOAuthApiBase):
    """Клиент Google OAuth API."""

    async def post_token(
        self,
        provider_config: OAuthProviderConfig,
        code: str,
        redirect_uri: str,
        code_verifier: str | None,
    ) -> GoogleOAuthTokenResponseSchema | NoReturn:
        """Метод обмена authorization code на токены.

        Args:
            provider_config: Конфиг провайдера google.
            code: Код авторизации из callback.
            redirect_uri: Redirect URI, использованный при запросе кода.
            code_verifier: PKCE code_verifier или None.

        Returns:
            Схема ответа.
        """
        body = GoogleOAuthTokenRequestBodySchema(
            code=code,
            client_id=provider_config.client_id,
            client_secret=provider_config.client_secret,
            redirect_uri=redirect_uri,
            grant_type="authorization_code",
            code_verifier=code_verifier,
        )

        response = await self.post(
            endpoint=provider_config.token_url,
            data=body.model_dump(exclude_none=True),
        )
        return GoogleOAuthTokenResponseSchema.model_validate(response.json())

    async def get_tokeninfo(
        self,
        provider_config: OAuthProviderConfig,
        id_token: str,
    ) -> GoogleOAuthTokenInfoResponseSchema | NoReturn:
        """Метод получения claims из id_token (GET tokeninfo).

        Args:
            provider_config: Конфиг провайдера google.
            id_token: JWT id_token от Google.

        Returns:
            Схема ответа tokeninfo.
        """
        query = GoogleOAuthTokenInfoQuerySchema(id_token=id_token)

        response = await self.get(
            endpoint=provider_config.tokeninfo_url,
            params=query.model_dump(),
        )
        return GoogleOAuthTokenInfoResponseSchema.model_validate(response.json())
