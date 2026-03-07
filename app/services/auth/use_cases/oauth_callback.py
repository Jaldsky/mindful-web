import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import NoReturn

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.models.tables import User
from ....integrations.google import GoogleOAuthApi
from ....schemas.integrations.google import (
    GoogleOAuthTokenInfoResponseSchema,
    GoogleOAuthTokenResponseSchema,
)
from ...normalizers import normalize_email
from ..common import create_tokens
from ..constants import MAX_UNIQUE_USERNAME_ATTEMPTS, MAX_USERNAME_LENGTH
from ..config import OAUTH_PROVIDER_CONFIGS, OAuthProviderConfig
from ..exceptions import (
    AuthServiceException,
    OAuthCodeExchangeFailedException,
    OAuthEmailMissingException,
    OAuthEmailNotVerifiedException,
    OAuthProviderUnsupportedException,
    OAuthRedirectUriMismatchException,
)
from ..queries import (
    fetch_user_by_email_any_status,
    fetch_user_by_oauth_provider_subject_any_status,
    fetch_taken_usernames_any_status,
)
from ..normalizers import AuthServiceNormalizers
from ..types import (
    AccessToken,
    OAuthAuthorizationCode,
    OAuthCodeVerifier,
    OAuthIdToken,
    OAuthProviderName,
    OAuthProviderSubject,
    OAuthRedirectUri,
    RefreshToken,
)
from ...types import Email, Username
from ..validators import AuthServiceValidators

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OAuthIdentity:
    """Идентичность пользователя из OAuth claims."""

    provider_subject: OAuthProviderSubject
    email: Email
    username_source: str


class OAuthCallbackServiceBase:
    """Базовый класс с общими OAuth callback операциями."""

    @staticmethod
    def _normalize_provider(provider: OAuthProviderName) -> OAuthProviderName:
        """Приватный метод нормализации имени OAuth-провайдера.

        Args:
            provider: Имя провайдера.

        Returns:
            Нормализованное имя провайдера.
        """
        return AuthServiceNormalizers.normalize_oauth_provider(provider)

    @staticmethod
    def _normalize_email_verified_flag(value: bool | None) -> bool:
        """Приватный метод нормализации флага подтверждения email.

        Args:
            value: Значение флага от провайдера.

        Returns:
            Нормализованный флаг.
        """
        return AuthServiceNormalizers.normalize_email_verified_flag(value)

    @staticmethod
    def _normalize_username(username: str) -> str:
        """Приватный метод нормализации сырой строки в базу для username.

        Args:
            username: Сырая строка.

        Returns:
            Нормализованная строка-база для username.
        """
        return AuthServiceNormalizers.normalize_oauth_username(username)

    @staticmethod
    def _validate_redirect_uri(
        provider_config: OAuthProviderConfig, redirect_uri: OAuthRedirectUri
    ) -> None | NoReturn:
        """Приватный метод проверки совпадения redirect_uri с конфигом провайдера.

        Args:
            provider_config: Конфиг OAuth-провайдера.
            redirect_uri: Redirect URI из запроса.

        Raises:
            OAuthRedirectUriMismatchException: Если redirect_uri не совпадает с конфигом.
        """
        AuthServiceValidators.validate_oauth_redirect_uri_matches(provider_config.redirect_uri, redirect_uri)

    def _get_provider_config(self, provider: OAuthProviderName) -> OAuthProviderConfig | NoReturn:
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


class OAuthCallbackService(OAuthCallbackServiceBase):
    """Сервис обработки OAuth callback."""

    def __init__(self, oauth_client: GoogleOAuthApi | None = None) -> None:
        """Инициализация сервиса OAuth callback.

        Args:
            oauth_client: Клиент OAuth API провайдера.
        """
        self._oauth_client = oauth_client or GoogleOAuthApi()

    async def _exchange_code_for_tokens(
        self,
        provider_config: OAuthProviderConfig,
        code: OAuthAuthorizationCode,
        redirect_uri: OAuthRedirectUri,
        code_verifier: OAuthCodeVerifier | None,
    ) -> GoogleOAuthTokenResponseSchema | NoReturn:
        """Приватный метод обмена authorization code на токены.

        Args:
            provider_config: Конфиг OAuth-провайдера.
            code: Код авторизации из callback.
            redirect_uri: Redirect URI, использованный при запросе кода.
            code_verifier: PKCE code_verifier или None.

        Returns:
            Схема ответа.
        """
        return await self._oauth_client.post_token(
            provider_config=provider_config,
            code=code,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
        )

    async def _fetch_claims(
        self, provider_config: OAuthProviderConfig, id_token: OAuthIdToken
    ) -> GoogleOAuthTokenInfoResponseSchema | NoReturn:
        """Приватный метод получения claims из id_token через клиент провайдера.

        Args:
            provider_config: Конфиг OAuth-провайдера.
            id_token: JWT id_token от провайдера.

        Returns:
            Схема ответа.
        """
        return await self._oauth_client.get_tokeninfo(provider_config=provider_config, id_token=id_token)

    def _make_username_candidate(self, base: str, suffix: int) -> Username:
        """Приватный метод формирования кандидата username из нормализованной базы и суффикса.

        Args:
            base: Нормализованная база для username (a-z0-9_).
            suffix: Суффикс (0 = без суффикса, иначе число).

        Returns:
            Строка-кандидат username.
        """
        suffix_str = "" if suffix == 0 else str(suffix)
        max_base_length = MAX_USERNAME_LENGTH - len(suffix_str)
        return f"{base[:max_base_length].strip('_')}{suffix_str}"

    async def _generate_unique_username(self, session: AsyncSession, source: str) -> Username | NoReturn:
        """Приватный метод подбора свободного username.

        Args:
            session: Сессия базы данных.
            source: Сырая строка для генерации базы.

        Returns:
            Свободный username.

        Raises:
            AuthServiceException: Если не удалось подобрать свободный username за отведённое число попыток.
        """
        base = self._normalize_username(source)
        candidates = [self._make_username_candidate(base, suffix) for suffix in range(MAX_UNIQUE_USERNAME_ATTEMPTS)]
        taken_usernames = await fetch_taken_usernames_any_status(session, candidates)
        for candidate in candidates:
            if candidate not in taken_usernames:
                return candidate
        raise AuthServiceException(
            key="auth.errors.auth_service_error",
            fallback="Failed to generate unique username",
        )

    @staticmethod
    def _reactivate_and_touch_user(user: User, now: datetime) -> None:
        """Приватный метод снятия soft-delete и обновления updated_at.

        Обновление updated_at выполняется всегда, так как факт OAuth-входа/линковки
        считается изменением пользовательской записи.

        Args:
            user: Объект пользователя.
            now: Текущее время (UTC).
        """
        if user.deleted_at is not None:
            user.deleted_at = None
        user.updated_at = now

    def _link_user_to_provider(
        self, user: User, provider: OAuthProviderName, provider_subject: OAuthProviderSubject, now: datetime
    ) -> None:
        """Приватный метод привязки пользователя к OAuth-провайдеру и обновления флага is_verified.

        Args:
            user: Объект пользователя.
            provider: Имя OAuth-провайдера.
            provider_subject: Идентификатор пользователя у провайдера.
            now: Текущее время (UTC).
        """
        self._reactivate_and_touch_user(user, now)
        user.oauth_provider = provider
        user.oauth_provider_subject = provider_subject
        user.is_verified = True

    async def _find_and_link_existing_user(
        self,
        session: AsyncSession,
        provider: OAuthProviderName,
        provider_subject: OAuthProviderSubject,
        email: Email,
        *,
        flush_if_email_linked: bool,
    ) -> User | None:
        """Приватный метод поиска существующего пользователя по провайдеру или email и привязки к провайдеру.

        Сначала ищет по (provider, provider_subject), затем по email. При найденном по email
        линкует пользователя к провайдеру и при необходимости выполняет flush.

        Args:
            session: Сессия базы данных.
            provider: Имя OAuth-провайдера.
            provider_subject: Идентификатор пользователя у провайдера.
            email: Email пользователя.
            flush_if_email_linked: Выполнить flush после линковки по email.

        Returns:
            Найденный и при необходимости обновлённый User или None.
        """
        now = datetime.now(timezone.utc)

        by_provider = await fetch_user_by_oauth_provider_subject_any_status(session, provider, provider_subject)
        if by_provider is not None:
            self._reactivate_and_touch_user(by_provider, now)
            return by_provider

        by_email = await fetch_user_by_email_any_status(session, email)
        if by_email is None:
            return None

        self._link_user_to_provider(by_email, provider, provider_subject, now)
        if flush_if_email_linked:
            await session.flush()
        return by_email

    async def _create_user(
        self,
        session: AsyncSession,
        provider: OAuthProviderName,
        provider_subject: OAuthProviderSubject,
        email: Email,
        username_source: str,
    ) -> User:
        """Приватный метод создания пользователя через OAuth.

        Процесс включает:
        1. Подбор уникального username по username_source
        2. Создание объекта User с привязкой к провайдеру
        3. Добавление в сессию и flush

        Args:
            session: Сессия базы данных.
            provider: Имя OAuth-провайдера.
            provider_subject: Идентификатор пользователя у провайдера.
            email: Email пользователя.
            username_source: Сырая строка для генерации username.

        Returns:
            Созданный объект User.
        """
        now = datetime.now(timezone.utc)
        username = await self._generate_unique_username(session, username_source)
        user = User(
            username=username,
            email=email,
            password=None,
            oauth_provider=provider,
            oauth_provider_subject=provider_subject,
            is_verified=True,
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        await session.flush()
        return user

    async def _resolve_or_create_user(
        self,
        session: AsyncSession,
        provider: OAuthProviderName,
        provider_subject: OAuthProviderSubject,
        email: Email,
        username_source: str,
    ) -> User:
        """Приватный метод поиска существующего пользователя или создания нового.

        Args:
            session: Сессия базы данных.
            provider: Имя OAuth-провайдера.
            provider_subject: Идентификатор пользователя у провайдера.
            email: Email пользователя.
            username_source: Сырая строка для генерации username.

        Returns:
            Существующий или созданный User.
        """
        existing_user = await self._find_and_link_existing_user(
            session=session,
            provider=provider,
            provider_subject=provider_subject,
            email=email,
            flush_if_email_linked=False,
        )
        if existing_user is not None:
            return existing_user
        return await self._create_user(session, provider, provider_subject, email, username_source)

    async def _recover_after_integrity_error(
        self,
        session: AsyncSession,
        provider: OAuthProviderName,
        provider_subject: OAuthProviderSubject,
        email: Email,
    ) -> User | None:
        """Приватный метод восстановления/связывания пользователя после гонки уникальных ограничений.

        Args:
            session: Сессия базы данных.
            provider: Имя OAuth-провайдера.
            provider_subject: Идентификатор пользователя у провайдера.
            email: Email пользователя.

        Returns:
            Найденный/обновлённый User или None.
        """
        return await self._find_and_link_existing_user(
            session=session,
            provider=provider,
            provider_subject=provider_subject,
            email=email,
            flush_if_email_linked=True,
        )

    async def _exchange_and_validate_claims(
        self,
        provider_config: OAuthProviderConfig,
        code: OAuthAuthorizationCode,
        redirect_uri: OAuthRedirectUri,
        code_verifier: OAuthCodeVerifier | None,
    ) -> GoogleOAuthTokenInfoResponseSchema | NoReturn:
        """Приватный метод обмена кода на токены, запроса claims и проверки aud/iss.

        Args:
            provider_config: Конфиг OAuth-провайдера.
            code: Код авторизации.
            redirect_uri: Redirect URI.
            code_verifier: PKCE code_verifier или None.

        Returns:
            Валидированные claims.

        Raises:
            OAuthCodeExchangeFailedException: При ошибке обмена, запроса или несовпадении aud/iss.
        """
        try:
            token_data = await self._exchange_code_for_tokens(provider_config, code, redirect_uri, code_verifier)
        except Exception as exc:
            raise OAuthCodeExchangeFailedException(
                key="auth.errors.oauth_code_exchange_failed",
                fallback="Failed to exchange OAuth code",
            ) from exc

        try:
            claims = await self._fetch_claims(provider_config, token_data.id_token)
        except Exception as exc:
            raise OAuthCodeExchangeFailedException(
                key="auth.errors.oauth_code_exchange_failed",
                fallback="Failed to validate OAuth token",
            ) from exc

        if claims.aud != provider_config.client_id:
            raise OAuthCodeExchangeFailedException(
                key="auth.errors.oauth_code_exchange_failed",
                fallback="OAuth token audience mismatch",
            )
        if claims.iss not in provider_config.allowed_issuers:
            raise OAuthCodeExchangeFailedException(
                key="auth.errors.oauth_code_exchange_failed",
                fallback="OAuth token issuer mismatch",
            )
        return claims

    def _extract_identity(self, claims: GoogleOAuthTokenInfoResponseSchema) -> OAuthIdentity | NoReturn:
        """Приватный метод извлечения идентичности пользователя из claims провайдера.

        Args:
            claims: Ответ tokeninfo провайдера.

        Returns:
            OAuthIdentity с provider_subject, email, username_source.

        Raises:
            OAuthCodeExchangeFailedException: Если отсутствует sub.
            OAuthEmailMissingException: Если отсутствует или пустой email.
            OAuthEmailNotVerifiedException: Если email не подтверждён у провайдера.
        """
        provider_subject = claims.sub.strip()
        email = normalize_email(claims.email or "")

        if not provider_subject:
            raise OAuthCodeExchangeFailedException(
                key="auth.errors.oauth_code_exchange_failed",
                fallback="Failed to validate OAuth token",
            )
        if not email:
            raise OAuthEmailMissingException(
                key="auth.errors.oauth_email_missing",
                fallback="OAuth provider did not return email",
            )
        if not self._normalize_email_verified_flag(claims.email_verified):
            raise OAuthEmailNotVerifiedException(
                key="auth.errors.oauth_email_not_verified",
                fallback="OAuth provider email is not verified",
            )

        username_source = (claims.name or email.split("@")[0] or "user").strip()
        return OAuthIdentity(
            provider_subject=provider_subject,
            email=email,
            username_source=username_source,
        )

    async def _resolve_user_with_integrity_retry(
        self,
        session: AsyncSession,
        provider: OAuthProviderName,
        identity: OAuthIdentity,
    ) -> User:
        """Приватный метод поиска/создания пользователя с повтором при IntegrityError.

        При IntegrityError (гонка при создании или линковке) выполняется rollback,
        затем повторный поиск/линковка через _recover_after_integrity_error.

        Args:
            session: Сессия базы данных.
            provider: Имя OAuth-провайдера.
            identity: Идентичность пользователя.

        Returns:
            Существующий или созданный User.
        """
        try:
            return await self._resolve_or_create_user(
                session=session,
                provider=provider,
                provider_subject=identity.provider_subject,
                email=identity.email,
                username_source=identity.username_source,
            )
        except IntegrityError:
            await session.rollback()
            recovered_user = await self._recover_after_integrity_error(
                session=session,
                provider=provider,
                provider_subject=identity.provider_subject,
                email=identity.email,
            )
            if recovered_user is None:
                raise
            return recovered_user

    async def exec(
        self,
        session: AsyncSession,
        provider: OAuthProviderName,
        code: OAuthAuthorizationCode,
        redirect_uri: OAuthRedirectUri,
        code_verifier: OAuthCodeVerifier | None = None,
    ) -> tuple[User, AccessToken, RefreshToken] | NoReturn:
        """Метод обработки OAuth callback.

        Процесс включает:
        1. Получение конфига провайдера и проверку redirect_uri
        2. Обмен кода на токены и запрос claims
        3. Извлечение идентичности из claims
        4. Поиск или создание пользователя
        5. Выпуск access/refresh токенов и коммит транзакции

        Args:
            session: Сессия базы данных.
            provider: Имя провайдера.
            code: Код авторизации из callback.
            redirect_uri: Redirect URI, использованный при запросе кода.
            code_verifier: PKCE code_verifier или None.

        Returns:
            Кортеж (user, access_token, refresh_token).

        Raises:
            OAuthProviderUnsupportedException: Провайдер не поддерживается.
            OAuthRedirectUriMismatchException: redirect_uri не совпадает с конфигом.
            OAuthCodeExchangeFailedException: Ошибка обмена кода или проверки токена/claims.
            OAuthEmailMissingException: Провайдер не вернул email.
            OAuthEmailNotVerifiedException: Email не подтверждён у провайдера.
            AuthServiceException: При непредвиденной ошибке.
        """
        try:
            provider_config = self._get_provider_config(provider)
            normalized_provider = provider_config.provider

            self._validate_redirect_uri(provider_config, redirect_uri)

            claims = await self._exchange_and_validate_claims(provider_config, code, redirect_uri, code_verifier)
            identity = self._extract_identity(claims)
            user = await self._resolve_user_with_integrity_retry(session, normalized_provider, identity)

            access_token, refresh_token = create_tokens(user.id)
            await session.commit()
            logger.info(f"OAuth callback successful for user_id={user.id} provider={normalized_provider}")
            return user, access_token, refresh_token

        except (
            OAuthProviderUnsupportedException,
            OAuthRedirectUriMismatchException,
            OAuthCodeExchangeFailedException,
            OAuthEmailMissingException,
            OAuthEmailNotVerifiedException,
            IntegrityError,
        ):
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise AuthServiceException(
                key="auth.errors.auth_service_error",
                fallback="Authentication service error",
            )
