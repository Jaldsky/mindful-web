import secrets
from typing import cast
from urllib.parse import urlencode, urlparse, urlunparse

from ..config import OAUTH_PROVIDER_CONFIGS, OAuthProviderConfig
from ..constants import OAUTH_STATE_TOKEN_BYTES
from ..exceptions import OAuthProviderUnsupportedException
from ..normalizers import AuthServiceNormalizers
from ..types import OAuthProviderName, OAuthState
from ....schemas.auth.oauth.authorize import OAuthAuthorizeQueryParamsSchema


class OAuthAuthorizeServiceBase:
    """Базовый класс с общими операциями для OAuth authorize."""

    @staticmethod
    def _normalize_provider(provider: OAuthProviderName) -> OAuthProviderName:
        """Приватный метод нормализации имени OAuth-провайдера.

        Args:
            provider: Имя провайдера.

        Returns:
            Нормализованное имя провайдера.
        """
        return AuthServiceNormalizers.normalize_oauth_provider(provider)

    def _get_provider_config(self, provider: OAuthProviderName) -> OAuthProviderConfig:
        """Приватный метод получения конфига OAuth-провайдера по имени.

        Args:
            provider: Имя провайдера.

        Returns:
            Конфиг провайдера.

        Raises:
            OAuthProviderUnsupportedException: Если провайдер не поддерживается.
        """
        normalized_provider = self._normalize_provider(provider)
        provider_config = OAUTH_PROVIDER_CONFIGS.get(normalized_provider)
        if provider_config is None:
            raise OAuthProviderUnsupportedException(
                key="auth.errors.oauth_provider_unsupported",
                fallback="OAuth provider is not supported",
            )
        return provider_config


class OAuthAuthorizeService(OAuthAuthorizeServiceBase):
    """Сервис OAuth authorize."""

    @staticmethod
    def _build_authorize_query_params(provider_config: OAuthProviderConfig, state: OAuthState) -> dict[str, str]:
        """Приватный метод сборки query-параметры для authorization URL.

        Args:
            provider_config: Конфиг OAuth-провайдера.
            state: Строка state (CSRF token).

        Returns:
            Словарь параметров для urlencode.
        """
        schema = OAuthAuthorizeQueryParamsSchema(
            client_id=provider_config.client_id,
            redirect_uri=provider_config.redirect_uri,
            scope=provider_config.auth_scope,
            state=state,
        )
        return schema.model_dump()

    def exec(self, provider: OAuthProviderName) -> tuple[str, OAuthState]:
        """Метод формирования authorization URL и state для редиректа пользователя к OAuth-провайдеру.

        Процесс:
        1. Получение конфига провайдера по имени
        2. Генерация криптостойкого state
        3. Сборка query-параметров и формирование authorization URL

        Args:
            provider: Имя провайдера.

        Returns:
            Кортеж (authorization_url, state).

        Raises:
            OAuthProviderUnsupportedException: Если провайдер не поддерживается.
        """
        provider_config = self._get_provider_config(provider)
        state: OAuthState = secrets.token_urlsafe(OAUTH_STATE_TOKEN_BYTES)
        query = urlencode(self._build_authorize_query_params(provider_config, state))
        parsed = urlparse(provider_config.auth_url)
        authorization_url = cast(str, urlunparse(parsed._replace(query=query)))
        return authorization_url, state
