from unittest import TestCase
from unittest.mock import patch

from app.services.auth.config import OAuthProviderConfig
from app.services.auth.exceptions import OAuthProviderUnsupportedException
from app.services.auth.use_cases.oauth_authorize import (
    OAuthAuthorizeService,
    OAuthAuthorizeServiceBase,
)


def _google_config() -> OAuthProviderConfig:
    return OAuthProviderConfig(
        provider="google",
        client_id="test-client-id",
        client_secret="secret",
        redirect_uri="https://app.example.com/oauth/google/callback",
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        auth_scope="openid email profile",
        token_url="https://oauth2.googleapis.com/token",
        tokeninfo_url="https://oauth2.googleapis.com/tokeninfo",
        allowed_issuers=("https://accounts.google.com", "accounts.google.com"),
    )


class TestOAuthAuthorizeServiceBase(TestCase):
    """Тесты OAuthAuthorizeServiceBase."""

    def test_normalize_provider_strips_and_lowercases(self) -> None:
        self.assertEqual(OAuthAuthorizeServiceBase._normalize_provider("  Google  "), "google")

    def test_get_provider_config_returns_config_when_configured(self) -> None:
        config = _google_config()
        service = OAuthAuthorizeServiceBase()
        with patch("app.services.auth.use_cases.oauth_authorize.OAUTH_PROVIDER_CONFIGS", {"google": config}):
            result = service._get_provider_config("google")
        self.assertIs(result, config)

    def test_get_provider_config_normalizes_provider_name(self) -> None:
        config = _google_config()
        service = OAuthAuthorizeServiceBase()
        with patch("app.services.auth.use_cases.oauth_authorize.OAUTH_PROVIDER_CONFIGS", {"google": config}):
            result = service._get_provider_config("  Google  ")
        self.assertIs(result, config)

    def test_get_provider_config_raises_unsupported(self) -> None:
        service = OAuthAuthorizeServiceBase()
        with patch("app.services.auth.use_cases.oauth_authorize.OAUTH_PROVIDER_CONFIGS", {}):
            with self.assertRaises(OAuthProviderUnsupportedException):
                service._get_provider_config("unknown")


class TestOAuthAuthorizeServiceBuildQueryParams(TestCase):
    """Тесты _build_authorize_query_params."""

    def test_returns_dict_with_config_values_and_fixed_params(self) -> None:
        config = _google_config()
        state = "my-state-token"
        result = OAuthAuthorizeService._build_authorize_query_params(config, state)
        self.assertEqual(result["client_id"], config.client_id)
        self.assertEqual(result["redirect_uri"], config.redirect_uri)
        self.assertEqual(result["scope"], config.auth_scope)
        self.assertEqual(result["state"], state)
        self.assertEqual(result["response_type"], "code")
        self.assertEqual(result["access_type"], "offline")
        self.assertEqual(result["include_granted_scopes"], "true")
        self.assertEqual(result["prompt"], "consent")

    def test_result_has_only_expected_keys(self) -> None:
        config = _google_config()
        result = OAuthAuthorizeService._build_authorize_query_params(config, "state")
        expected_keys = {
            "client_id",
            "redirect_uri",
            "response_type",
            "scope",
            "state",
            "access_type",
            "include_granted_scopes",
            "prompt",
        }
        self.assertEqual(set(result.keys()), expected_keys)


class TestOAuthAuthorizeServiceExec(TestCase):
    """Тесты exec OAuthAuthorizeService."""

    def test_exec_returns_tuple_url_and_state(self) -> None:
        config = _google_config()
        with patch("app.services.auth.use_cases.oauth_authorize.OAUTH_PROVIDER_CONFIGS", {"google": config}):
            with patch(
                "app.services.auth.use_cases.oauth_authorize.secrets.token_urlsafe", return_value="fixed-state"
            ):
                service = OAuthAuthorizeService()
                url, state = service.exec("google")
        self.assertIsInstance(url, str)
        self.assertIsInstance(state, str)
        self.assertEqual(state, "fixed-state")

    def test_exec_url_starts_with_auth_url_and_contains_query(self) -> None:
        config = _google_config()
        with patch("app.services.auth.use_cases.oauth_authorize.OAUTH_PROVIDER_CONFIGS", {"google": config}):
            with patch("app.services.auth.use_cases.oauth_authorize.secrets.token_urlsafe", return_value="st"):
                service = OAuthAuthorizeService()
                url, _ = service.exec("google")
        self.assertTrue(url.startswith(config.auth_url))
        self.assertIn("?", url)
        query = url.split("?", 1)[1]
        self.assertIn("client_id=test-client-id", query)
        self.assertIn("redirect_uri=", query)
        self.assertIn("response_type=code", query)
        self.assertIn("scope=openid+email+profile", query)
        self.assertIn("state=st", query)
        self.assertIn("access_type=offline", query)
        self.assertIn("prompt=consent", query)

    def test_exec_state_is_urlsafe_and_non_empty(self) -> None:
        config = _google_config()
        with patch("app.services.auth.use_cases.oauth_authorize.OAUTH_PROVIDER_CONFIGS", {"google": config}):
            service = OAuthAuthorizeService()
            _, state = service.exec("google")
        self.assertTrue(len(state) > 0)
        for c in state:
            self.assertIn(
                c,
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_",
                msg=f"state must be url-safe, got {state!r}",
            )

    def test_exec_raises_unsupported_provider(self) -> None:
        service = OAuthAuthorizeService()
        with patch("app.services.auth.use_cases.oauth_authorize.OAUTH_PROVIDER_CONFIGS", {}):
            with self.assertRaises(OAuthProviderUnsupportedException):
                service.exec("unknown")

    def test_exec_uses_normalized_provider(self) -> None:
        config = _google_config()
        with patch("app.services.auth.use_cases.oauth_authorize.OAUTH_PROVIDER_CONFIGS", {"google": config}):
            with patch("app.services.auth.use_cases.oauth_authorize.secrets.token_urlsafe", return_value="s"):
                service = OAuthAuthorizeService()
                url, _ = service.exec("  Google  ")
        self.assertTrue(url.startswith(config.auth_url))
        self.assertIn("client_id=test-client-id", url)
