import asyncio
import os
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

from app.db.models.base import Base
from app.db.models.tables import User
from app.db.session.manager import ManagerAsync
from app.schemas.integrations.google import (
    GoogleOAuthTokenInfoResponseSchema,
    GoogleOAuthTokenResponseSchema,
)
from app.services.auth.common import decode_token, hash_password
from app.services.auth.config import OAuthProviderConfig
from app.services.auth.exceptions import (
    AuthServiceException,
    OAuthCodeExchangeFailedException,
    OAuthEmailMissingException,
    OAuthEmailNotVerifiedException,
    OAuthProviderUnsupportedException,
    OAuthRedirectUriMismatchException,
)
from app.services.auth.use_cases.oauth_callback import (
    OAuthCallbackService,
    OAuthCallbackServiceBase,
    OAuthIdentity,
)


class TestOAuthCallbackService(TestCase):
    def setUp(self) -> None:
        self.logger = Mock()
        self.database_url = "sqlite+aiosqlite:///:memory:"

    def _run_async(self, coro):
        return asyncio.run(coro)

    def _patch_server_defaults_for_sqlite(self):
        original_user_created = User.created_at.property.columns[0].server_default
        original_user_updated = User.updated_at.property.columns[0].server_default
        User.created_at.property.columns[0].server_default = None
        User.updated_at.property.columns[0].server_default = None
        return original_user_created, original_user_updated

    def _restore_server_defaults(self, original_user_created, original_user_updated):
        User.created_at.property.columns[0].server_default = original_user_created
        User.updated_at.property.columns[0].server_default = original_user_updated

    @staticmethod
    def _redirect_uri() -> str:
        return os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:5173/oauth/google/callback")

    def _google_config(self) -> OAuthProviderConfig:
        """Конфиг google для тестов (redirect_uri совпадает с _redirect_uri())."""
        return OAuthProviderConfig(
            provider="google",
            client_id="client-id",
            client_secret="secret",
            redirect_uri=self._redirect_uri(),
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            auth_scope="openid email profile",
            token_url="https://oauth2.googleapis.com/token",
            tokeninfo_url="https://oauth2.googleapis.com/tokeninfo",
            allowed_issuers=("https://accounts.google.com", "accounts.google.com"),
        )

    def test_exec_creates_new_oauth_user(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                with patch(
                    "app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS",
                    {"google": self._google_config()},
                ):
                    manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                    engine = manager.get_engine()
                    async with engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)

                    async with manager.get_session() as session:
                        service = OAuthCallbackService()
                        service._exchange_code_for_tokens = AsyncMock(
                            return_value=GoogleOAuthTokenResponseSchema(id_token="token")
                        )
                        service._fetch_claims = AsyncMock(
                            return_value=GoogleOAuthTokenInfoResponseSchema(
                                iss="https://accounts.google.com",
                                aud="client-id",
                                sub="google-sub-1",
                                email="new.user@example.com",
                                email_verified=True,
                                name="New User",
                            )
                        )

                        user, access_token, refresh_token = await service.exec(
                            session=session,
                            provider="google",
                            code="oauth-code",
                            redirect_uri=self._redirect_uri(),
                        )

                        self.assertEqual(user.oauth_provider, "google")
                        self.assertEqual(user.oauth_provider_subject, "google-sub-1")
                        self.assertEqual(user.email, "new.user@example.com")
                        self.assertTrue(user.is_verified)
                        self.assertEqual(decode_token(access_token).get("sub"), str(user.id))
                        self.assertEqual(decode_token(refresh_token).get("sub"), str(user.id))

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_links_existing_local_user_by_email(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                with patch(
                    "app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS",
                    {"google": self._google_config()},
                ):
                    manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                    engine = manager.get_engine()
                    async with engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)

                    now = datetime.now(timezone.utc)
                    async with manager.get_session() as session:
                        user = User(
                            username="existing",
                            email="existing@example.com",
                            password=hash_password("password123", rounds=4),
                            is_verified=False,
                            created_at=now,
                            updated_at=now,
                        )
                        session.add(user)
                        await session.commit()
                        existing_id = user.id

                    async with manager.get_session() as session:
                        service = OAuthCallbackService()
                        service._exchange_code_for_tokens = AsyncMock(  # type: ignore[method-assign]
                            return_value=GoogleOAuthTokenResponseSchema(id_token="token")
                        )
                        service._fetch_claims = AsyncMock(  # type: ignore[method-assign]
                            return_value=GoogleOAuthTokenInfoResponseSchema(
                                iss="https://accounts.google.com",
                                aud="client-id",
                                sub="google-sub-2",
                                email="existing@example.com",
                                email_verified=True,
                                name="Existing User",
                            )
                        )

                        user, _, _ = await service.exec(
                            session=session,
                            provider="google",
                            code="oauth-code",
                            redirect_uri=self._redirect_uri(),
                        )

                        self.assertEqual(user.id, existing_id)
                        self.assertEqual(user.oauth_provider, "google")
                        self.assertEqual(user.oauth_provider_subject, "google-sub-2")
                        self.assertTrue(user.is_verified)

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_raises_when_email_missing(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                with patch(
                    "app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS",
                    {"google": self._google_config()},
                ):
                    manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                    engine = manager.get_engine()
                    async with engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)

                    async with manager.get_session() as session:
                        service = OAuthCallbackService()
                        service._exchange_code_for_tokens = AsyncMock(  # type: ignore[method-assign]
                            return_value=GoogleOAuthTokenResponseSchema(id_token="token")
                        )
                        service._fetch_claims = AsyncMock(  # type: ignore[method-assign]
                            return_value=GoogleOAuthTokenInfoResponseSchema(
                                iss="https://accounts.google.com",
                                aud="client-id",
                                sub="google-sub-3",
                                email=None,
                                email_verified=True,
                                name="No Email",
                            )
                        )

                        with self.assertRaises(OAuthEmailMissingException):
                            await service.exec(
                                session=session,
                                provider="google",
                                code="oauth-code",
                                redirect_uri=self._redirect_uri(),
                            )

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_raises_when_email_not_verified(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                with patch(
                    "app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS",
                    {"google": self._google_config()},
                ):
                    manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                    engine = manager.get_engine()
                    async with engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)

                    async with manager.get_session() as session:
                        service = OAuthCallbackService()
                        service._exchange_code_for_tokens = AsyncMock(
                            return_value=GoogleOAuthTokenResponseSchema(id_token="token")
                        )
                        service._fetch_claims = AsyncMock(
                            return_value=GoogleOAuthTokenInfoResponseSchema(
                                iss="https://accounts.google.com",
                                aud="client-id",
                                sub="google-sub-4",
                                email="not.verified@example.com",
                                email_verified=False,
                                name="Not Verified",
                            )
                        )

                        with self.assertRaises(OAuthEmailNotVerifiedException):
                            await service.exec(
                                session=session,
                                provider="google",
                                code="oauth-code",
                                redirect_uri=self._redirect_uri(),
                            )

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_restores_soft_deleted_user_with_same_email(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                with patch(
                    "app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS",
                    {"google": self._google_config()},
                ):
                    manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                    engine = manager.get_engine()
                    async with engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)

                    now = datetime.now(timezone.utc)
                    async with manager.get_session() as session:
                        user = User(
                            username="soft_deleted_user",
                            email="soft.deleted@example.com",
                            password=None,
                            is_verified=False,
                            created_at=now,
                            updated_at=now,
                            deleted_at=now,
                        )
                        session.add(user)
                        await session.commit()

                    async with manager.get_session() as session:
                        service = OAuthCallbackService()
                        service._exchange_code_for_tokens = AsyncMock(
                            return_value=GoogleOAuthTokenResponseSchema(id_token="token")
                        )
                        service._fetch_claims = AsyncMock(
                            return_value=GoogleOAuthTokenInfoResponseSchema(
                                iss="https://accounts.google.com",
                                aud="client-id",
                                sub="google-soft-deleted-sub",
                                email="soft.deleted@example.com",
                                email_verified=True,
                                name="Soft Deleted",
                            )
                        )

                        user, _, _ = await service.exec(
                            session=session,
                            provider="google",
                            code="oauth-code",
                            redirect_uri=self._redirect_uri(),
                        )

                        self.assertIsNone(user.deleted_at)
                        self.assertEqual(user.oauth_provider, "google")
                        self.assertEqual(user.oauth_provider_subject, "google-soft-deleted-sub")
                        self.assertTrue(user.is_verified)

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_raises_unsupported_provider(self) -> None:
        """При неподдерживаемом провайдере выбрасывается OAuthProviderUnsupportedException."""

        async def _test() -> None:
            async with ManagerAsync(logger=self.logger, database_url=self.database_url).get_session() as session:
                service = OAuthCallbackService()
                with patch("app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS", {}):
                    with self.assertRaises(OAuthProviderUnsupportedException):
                        await service.exec(
                            session=session,
                            provider="unknown",
                            code="code",
                            redirect_uri="http://localhost/cb",
                        )

        self._run_async(_test())

    def test_exec_raises_redirect_uri_mismatch(self) -> None:
        """При несовпадении redirect_uri с конфигом выбрасывается OAuthRedirectUriMismatchException."""
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test() -> None:
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                config = OAuthProviderConfig(
                    provider="google",
                    client_id="cid",
                    client_secret="secret",
                    redirect_uri="https://app.example.com/oauth/callback",
                    auth_url="https://accounts.google.com/auth",
                    auth_scope="openid email",
                    token_url="https://oauth2.googleapis.com/token",
                    tokeninfo_url="https://oauth2.googleapis.com/tokeninfo",
                    allowed_issuers=("https://accounts.google.com",),
                )
                async with manager.get_session() as session:
                    service = OAuthCallbackService()
                    with patch(
                        "app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS", {"google": config}
                    ):
                        with self.assertRaises(OAuthRedirectUriMismatchException):
                            await service.exec(
                                session=session,
                                provider="google",
                                code="code",
                                redirect_uri="https://wrong.example.com/callback",
                            )

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_raises_exchange_failed(self) -> None:
        """При ошибке обмена кода выбрасывается OAuthCodeExchangeFailedException."""
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test() -> None:
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                config = OAuthProviderConfig(
                    provider="google",
                    client_id="cid",
                    client_secret="secret",
                    redirect_uri="https://app.example.com/cb",
                    auth_url="https://accounts.google.com/auth",
                    auth_scope="openid email",
                    token_url="https://oauth2.googleapis.com/token",
                    tokeninfo_url="https://oauth2.googleapis.com/tokeninfo",
                    allowed_issuers=("https://accounts.google.com",),
                )
                async with manager.get_session() as session:
                    service = OAuthCallbackService()
                    service._exchange_and_validate_claims = AsyncMock(
                        side_effect=OAuthCodeExchangeFailedException(
                            key="auth.errors.oauth_code_exchange_failed",
                            fallback="Failed to exchange OAuth code",
                        )
                    )
                    with patch(
                        "app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS", {"google": config}
                    ):
                        with self.assertRaises(OAuthCodeExchangeFailedException):
                            await service.exec(
                                session=session,
                                provider="google",
                                code="code",
                                redirect_uri="https://app.example.com/cb",
                            )

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_returns_existing_user_when_already_linked_by_provider(self) -> None:
        """При повторном входе по тому же провайдеру/sub возвращается тот же пользователь."""
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test() -> None:
                with patch(
                    "app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS",
                    {"google": self._google_config()},
                ):
                    manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                    engine = manager.get_engine()
                    async with engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)

                    now = datetime.now(timezone.utc)
                    async with manager.get_session() as session:
                        user = User(
                            username="oauth_user",
                            email="oauth@example.com",
                            password=None,
                            oauth_provider="google",
                            oauth_provider_subject="google-sub-same",
                            is_verified=True,
                            created_at=now,
                            updated_at=now,
                        )
                        session.add(user)
                        await session.commit()
                        existing_id = user.id

                    async with manager.get_session() as session:
                        service = OAuthCallbackService()
                        service._exchange_code_for_tokens = AsyncMock(
                            return_value=GoogleOAuthTokenResponseSchema(id_token="token")
                        )
                        service._fetch_claims = AsyncMock(
                            return_value=GoogleOAuthTokenInfoResponseSchema(
                                iss="https://accounts.google.com",
                                aud="client-id",
                                sub="google-sub-same",
                                email="oauth@example.com",
                                email_verified=True,
                                name="OAuth User",
                            )
                        )
                        returned_user, _, _ = await service.exec(
                            session=session,
                            provider="google",
                            code="code",
                            redirect_uri=self._redirect_uri(),
                        )
                        self.assertEqual(returned_user.id, existing_id)
                        self.assertEqual(returned_user.oauth_provider, "google")
                        self.assertEqual(returned_user.oauth_provider_subject, "google-sub-same")

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_raises_auth_service_exception_on_unexpected_error(self) -> None:
        """При непредвиденном исключении выполняется rollback и выбрасывается AuthServiceException."""
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test() -> None:
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                config = OAuthProviderConfig(
                    provider="google",
                    client_id="cid",
                    client_secret="secret",
                    redirect_uri="https://app.example.com/cb",
                    auth_url="https://accounts.google.com/auth",
                    auth_scope="openid",
                    token_url="https://oauth2.googleapis.com/token",
                    tokeninfo_url="https://oauth2.googleapis.com/tokeninfo",
                    allowed_issuers=("https://accounts.google.com",),
                )
                async with manager.get_session() as session:
                    service = OAuthCallbackService()
                    service._exchange_and_validate_claims = AsyncMock(  # type: ignore[method-assign]
                        return_value=GoogleOAuthTokenInfoResponseSchema(
                            sub="sub",
                            email="u@example.com",
                            email_verified=True,
                            iss="https://accounts.google.com",
                            aud="cid",
                            name="User",
                        )
                    )
                    service._resolve_user_with_integrity_retry = AsyncMock(  # type: ignore[method-assign]
                        side_effect=RuntimeError("unexpected")
                    )
                    with patch(
                        "app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS", {"google": config}
                    ):
                        with self.assertRaises(AuthServiceException):
                            await service.exec(
                                session=session,
                                provider="google",
                                code="code",
                                redirect_uri="https://app.example.com/cb",
                            )

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)


class TestOAuthCallbackServiceBase(TestCase):
    """Юнит-тесты OAuthCallbackServiceBase."""

    def test_normalize_provider_strips_and_lowercases(self) -> None:
        self.assertEqual(OAuthCallbackServiceBase._normalize_provider("  Google  "), "google")

    def test_normalize_email_verified_flag_true(self) -> None:
        self.assertTrue(OAuthCallbackServiceBase._normalize_email_verified_flag(True))
        self.assertTrue(OAuthCallbackServiceBase._normalize_email_verified_flag("true"))

    def test_normalize_email_verified_flag_false(self) -> None:
        self.assertFalse(OAuthCallbackServiceBase._normalize_email_verified_flag(False))
        self.assertFalse(OAuthCallbackServiceBase._normalize_email_verified_flag("false"))

    def test_normalize_username_delegates_to_normalizer(self) -> None:
        self.assertEqual(OAuthCallbackServiceBase._normalize_username("John Doe"), "john_doe")

    def test_validate_redirect_uri_match_passes(self) -> None:
        config = OAuthProviderConfig(
            provider="google",
            client_id="cid",
            client_secret="secret",
            redirect_uri="https://app.example.com/cb",
            auth_url="https://accounts.google.com/auth",
            auth_scope="openid",
            token_url="https://oauth2.googleapis.com/token",
            tokeninfo_url="https://oauth2.googleapis.com/tokeninfo",
            allowed_issuers=(),
        )
        OAuthCallbackServiceBase._validate_redirect_uri(config, "https://app.example.com/cb")

    def test_validate_redirect_uri_mismatch_raises(self) -> None:
        config = OAuthProviderConfig(
            provider="google",
            client_id="cid",
            client_secret="secret",
            redirect_uri="https://app.example.com/cb",
            auth_url="https://accounts.google.com/auth",
            auth_scope="openid",
            token_url="https://oauth2.googleapis.com/token",
            tokeninfo_url="https://oauth2.googleapis.com/tokeninfo",
            allowed_issuers=(),
        )
        with self.assertRaises(OAuthRedirectUriMismatchException):
            OAuthCallbackServiceBase._validate_redirect_uri(config, "https://other.com/cb")

    def test_get_provider_config_returns_config_when_configured(self) -> None:
        config = OAuthProviderConfig(
            provider="google",
            client_id="cid",
            client_secret="secret",
            redirect_uri="https://app.example.com/cb",
            auth_url="https://accounts.google.com/auth",
            auth_scope="openid",
            token_url="https://oauth2.googleapis.com/token",
            tokeninfo_url="https://oauth2.googleapis.com/tokeninfo",
            allowed_issuers=(),
        )
        service = OAuthCallbackServiceBase()
        with patch("app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS", {"google": config}):
            result = service._get_provider_config("google")
        self.assertIs(result, config)

    def test_get_provider_config_normalizes_provider_name(self) -> None:
        config = OAuthProviderConfig(
            provider="google",
            client_id="cid",
            client_secret="secret",
            redirect_uri="https://app.example.com/cb",
            auth_url="https://accounts.google.com/auth",
            auth_scope="openid",
            token_url="https://oauth2.googleapis.com/token",
            tokeninfo_url="https://oauth2.googleapis.com/tokeninfo",
            allowed_issuers=(),
        )
        service = OAuthCallbackServiceBase()
        with patch("app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS", {"google": config}):
            result = service._get_provider_config("  Google  ")
        self.assertIs(result, config)

    def test_get_provider_config_raises_unsupported(self) -> None:
        service = OAuthCallbackServiceBase()
        with patch("app.services.auth.use_cases.oauth_callback.OAUTH_PROVIDER_CONFIGS", {}):
            with self.assertRaises(OAuthProviderUnsupportedException):
                service._get_provider_config("unknown")


class TestOAuthCallbackServiceUnit(TestCase):
    """Юнит-тесты внутренних методов OAuthCallbackService."""

    def test_make_username_candidate_suffix_zero(self) -> None:
        service = OAuthCallbackService()
        self.assertEqual(service._make_username_candidate("myuser", 0), "myuser")

    def test_make_username_candidate_suffix_non_zero(self) -> None:
        service = OAuthCallbackService()
        self.assertEqual(service._make_username_candidate("myuser", 1), "myuser1")

    def test_make_username_candidate_truncates_base_if_needed(self) -> None:
        service = OAuthCallbackService()
        long_base = "a" * 50
        # suffix 99 -> "99", max_base_length = 50 - 2 = 48
        self.assertEqual(service._make_username_candidate(long_base, 99), "a" * 48 + "99")

    def test_extract_identity_success(self) -> None:
        service = OAuthCallbackService()
        claims = GoogleOAuthTokenInfoResponseSchema(
            sub="sub-123",
            email="user@example.com",
            email_verified=True,
            iss="https://accounts.google.com",
            aud="client-id",
            name="John Doe",
        )
        identity = service._extract_identity(claims)
        self.assertIsInstance(identity, OAuthIdentity)
        self.assertEqual(identity.provider_subject, "sub-123")
        self.assertEqual(identity.email, "user@example.com")
        self.assertEqual(identity.username_source, "John Doe")

    def test_extract_identity_username_source_from_email_when_no_name(self) -> None:
        service = OAuthCallbackService()
        claims = GoogleOAuthTokenInfoResponseSchema(
            sub="sub-456",
            email="jane@example.com",
            email_verified=True,
            iss="https://accounts.google.com",
            aud="client-id",
            name=None,
        )
        identity = service._extract_identity(claims)
        self.assertEqual(identity.username_source, "jane")

    def test_extract_identity_username_source_fallback_user(self) -> None:
        """Когда name отсутствует и префикс email — «user», username_source = «user»."""
        service = OAuthCallbackService()
        claims = GoogleOAuthTokenInfoResponseSchema(
            sub="sub-usr",
            email="user@example.com",
            email_verified=True,
            iss="https://accounts.google.com",
            aud="client-id",
            name=None,
        )
        identity = service._extract_identity(claims)
        self.assertEqual(identity.username_source, "user")

    def test_extract_identity_raises_when_sub_empty(self) -> None:
        service = OAuthCallbackService()
        claims = GoogleOAuthTokenInfoResponseSchema(
            sub="   ",
            email="user@example.com",
            email_verified=True,
            iss="https://accounts.google.com",
            aud="client-id",
            name="User",
        )
        with self.assertRaises(OAuthCodeExchangeFailedException):
            service._extract_identity(claims)

    def test_extract_identity_raises_when_email_missing(self) -> None:
        service = OAuthCallbackService()
        claims = GoogleOAuthTokenInfoResponseSchema(
            sub="sub-789",
            email=None,
            email_verified=True,
            iss="https://accounts.google.com",
            aud="client-id",
            name="User",
        )
        with self.assertRaises(OAuthEmailMissingException):
            service._extract_identity(claims)

    def test_extract_identity_raises_when_email_empty_after_normalize(self) -> None:
        service = OAuthCallbackService()
        claims = GoogleOAuthTokenInfoResponseSchema(
            sub="sub-789",
            email="   ",
            email_verified=True,
            iss="https://accounts.google.com",
            aud="client-id",
            name="User",
        )
        with self.assertRaises(OAuthEmailMissingException):
            service._extract_identity(claims)

    def test_extract_identity_raises_when_email_not_verified(self) -> None:
        service = OAuthCallbackService()
        claims = GoogleOAuthTokenInfoResponseSchema(
            sub="sub-999",
            email="user@example.com",
            email_verified=False,
            iss="https://accounts.google.com",
            aud="client-id",
            name="User",
        )
        with self.assertRaises(OAuthEmailNotVerifiedException):
            service._extract_identity(claims)

    def test_reactivate_and_touch_user_clears_deleted_at_and_updates_updated_at(self) -> None:
        now = datetime.now(timezone.utc)
        user = Mock(spec=User)
        user.deleted_at = now
        user.updated_at = None
        OAuthCallbackService._reactivate_and_touch_user(user, now)
        self.assertIsNone(user.deleted_at)
        self.assertEqual(user.updated_at, now)

    def test_reactivate_and_touch_user_only_updates_updated_at_when_not_deleted(self) -> None:
        now = datetime.now(timezone.utc)
        user = Mock(spec=User)
        user.deleted_at = None
        user.updated_at = None
        OAuthCallbackService._reactivate_and_touch_user(user, now)
        self.assertEqual(user.updated_at, now)

    def test_link_user_to_provider_sets_oauth_fields_and_verified(self) -> None:
        service = OAuthCallbackService()
        now = datetime.now(timezone.utc)
        user = Mock(spec=User)
        user.deleted_at = None
        user.updated_at = None
        user.oauth_provider = None
        user.oauth_provider_subject = None
        user.is_verified = False
        service._link_user_to_provider(user, "google", "sub-123", now)
        self.assertIsNone(user.deleted_at)
        self.assertEqual(user.updated_at, now)
        self.assertEqual(user.oauth_provider, "google")
        self.assertEqual(user.oauth_provider_subject, "sub-123")
        self.assertTrue(user.is_verified)

    def test_exchange_and_validate_claims_raises_on_aud_mismatch(self) -> None:
        """При несовпадении aud с client_id выбрасывается OAuthCodeExchangeFailedException."""
        config = OAuthProviderConfig(
            provider="google",
            client_id="expected-client-id",
            client_secret="secret",
            redirect_uri="https://app.example.com/cb",
            auth_url="https://accounts.google.com/auth",
            auth_scope="openid",
            token_url="https://oauth2.googleapis.com/token",
            tokeninfo_url="https://oauth2.googleapis.com/tokeninfo",
            allowed_issuers=("https://accounts.google.com",),
        )
        service = OAuthCallbackService()
        service._exchange_code_for_tokens = AsyncMock(  # type: ignore[method-assign]
            return_value=GoogleOAuthTokenResponseSchema(id_token="id")
        )
        service._fetch_claims = AsyncMock(  # type: ignore[method-assign]
            return_value=GoogleOAuthTokenInfoResponseSchema(
                sub="sub",
                email="u@example.com",
                email_verified=True,
                iss="https://accounts.google.com",
                aud="wrong-audience",
                name="User",
            )
        )

        async def _run() -> None:
            await service._exchange_and_validate_claims(config, "code", "https://app.example.com/cb", None)

        with self.assertRaises(OAuthCodeExchangeFailedException):
            asyncio.run(_run())

    def test_exchange_and_validate_claims_raises_on_iss_mismatch(self) -> None:
        """При несовпадении iss с allowed_issuers выбрасывается OAuthCodeExchangeFailedException."""
        config = OAuthProviderConfig(
            provider="google",
            client_id="cid",
            client_secret="secret",
            redirect_uri="https://app.example.com/cb",
            auth_url="https://accounts.google.com/auth",
            auth_scope="openid",
            token_url="https://oauth2.googleapis.com/token",
            tokeninfo_url="https://oauth2.googleapis.com/tokeninfo",
            allowed_issuers=("https://accounts.google.com",),
        )
        service = OAuthCallbackService()
        service._exchange_code_for_tokens = AsyncMock(  # type: ignore[method-assign]
            return_value=GoogleOAuthTokenResponseSchema(id_token="id")
        )
        service._fetch_claims = AsyncMock(  # type: ignore[method-assign]
            return_value=GoogleOAuthTokenInfoResponseSchema(
                sub="sub",
                email="u@example.com",
                email_verified=True,
                iss="https://evil.issuer.com",
                aud="cid",
                name="User",
            )
        )

        async def _run() -> None:
            await service._exchange_and_validate_claims(config, "code", "https://app.example.com/cb", None)

        with self.assertRaises(OAuthCodeExchangeFailedException):
            asyncio.run(_run())
