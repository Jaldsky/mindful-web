from unittest import TestCase

from app.services.auth.constants import (
    AUTH_OAUTH_STATE_COOKIE_NAME,
    MAX_USERNAME_LENGTH,
    MIN_USERNAME_LENGTH,
)
from app.services.auth.normalizers import AuthServiceNormalizers


class TestAuthServiceNormalizers(TestCase):
    """Тесты AuthServiceNormalizers."""

    def test_normalize_username_strips_and_lowercases(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_username("  MyUser  "),
            "myuser",
        )

    def test_normalize_username_none_returns_empty(self) -> None:
        self.assertEqual(AuthServiceNormalizers.normalize_username(None), "")

    def test_normalize_username_empty_string_returns_empty(self) -> None:
        self.assertEqual(AuthServiceNormalizers.normalize_username(""), "")

    def test_normalize_email_strips_and_lowercases(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_email("  Test@Example.COM  "),
            "test@example.com",
        )

    def test_normalize_email_none_returns_empty(self) -> None:
        self.assertEqual(AuthServiceNormalizers.normalize_email(None), "")

    def test_normalize_password_returns_as_is(self) -> None:
        self.assertEqual(AuthServiceNormalizers.normalize_password("secret"), "secret")

    def test_normalize_password_none_returns_empty(self) -> None:
        self.assertEqual(AuthServiceNormalizers.normalize_password(None), "")

    def test_normalize_password_empty_string_returns_empty(self) -> None:
        self.assertEqual(AuthServiceNormalizers.normalize_password(""), "")

    def test_normalize_jwt_token_strips(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_jwt_token("  eyJhbGc.xxx  "),
            "eyJhbGc.xxx",
        )

    def test_normalize_jwt_token_none_returns_empty(self) -> None:
        self.assertEqual(AuthServiceNormalizers.normalize_jwt_token(None), "")

    def test_normalize_oauth_provider_strips_and_lowercases(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_oauth_provider("  Google  "),
            "google",
        )

    def test_normalize_oauth_provider_none_returns_empty(self) -> None:
        self.assertEqual(AuthServiceNormalizers.normalize_oauth_provider(None), "")

    def test_normalize_email_verified_flag_true(self) -> None:
        self.assertTrue(AuthServiceNormalizers.normalize_email_verified_flag(True))

    def test_normalize_email_verified_flag_false(self) -> None:
        self.assertFalse(AuthServiceNormalizers.normalize_email_verified_flag(False))

    def test_normalize_email_verified_flag_string_true(self) -> None:
        self.assertTrue(AuthServiceNormalizers.normalize_email_verified_flag("true"))
        self.assertTrue(AuthServiceNormalizers.normalize_email_verified_flag("TRUE"))

    def test_normalize_email_verified_flag_string_false(self) -> None:
        self.assertFalse(AuthServiceNormalizers.normalize_email_verified_flag("false"))
        self.assertFalse(AuthServiceNormalizers.normalize_email_verified_flag(""))

    def test_normalize_email_verified_flag_other_returns_false(self) -> None:
        self.assertFalse(AuthServiceNormalizers.normalize_email_verified_flag(None))
        self.assertFalse(AuthServiceNormalizers.normalize_email_verified_flag(1))

    def test_normalize_oauth_state_cookie_name_prefixes_and_normalizes(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_oauth_state_cookie_name("  Google  "),
            f"{AUTH_OAUTH_STATE_COOKIE_NAME}_google",
        )

    def test_normalize_oauth_state_cookie_name_none_returns_prefix_only(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_oauth_state_cookie_name(None),
            f"{AUTH_OAUTH_STATE_COOKIE_NAME}_",
        )

    def test_normalize_oauth_code_strips(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_oauth_code("  4/0abc  "),
            "4/0abc",
        )

    def test_normalize_oauth_code_none_returns_empty(self) -> None:
        self.assertEqual(AuthServiceNormalizers.normalize_oauth_code(None), "")

    def test_normalize_oauth_redirect_uri_strips(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_oauth_redirect_uri("  https://app/cb  "),
            "https://app/cb",
        )

    def test_normalize_oauth_redirect_uri_none_returns_empty(self) -> None:
        self.assertEqual(AuthServiceNormalizers.normalize_oauth_redirect_uri(None), "")

    def test_normalize_oauth_code_verifier_strips(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_oauth_code_verifier("  verifier  "),
            "verifier",
        )

    def test_normalize_oauth_code_verifier_none_returns_none(self) -> None:
        self.assertIsNone(AuthServiceNormalizers.normalize_oauth_code_verifier(None))

    def test_normalize_oauth_state_strips(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_oauth_state("  state_value  "),
            "state_value",
        )

    def test_normalize_oauth_state_none_returns_none(self) -> None:
        self.assertIsNone(AuthServiceNormalizers.normalize_oauth_state(None))

    def test_normalize_oauth_username_lowercases_and_replaces_invalid_chars(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_oauth_username("John Doe"),
            "john_doe",
        )

    def test_normalize_oauth_username_collapses_underscores(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_oauth_username("a---b"),
            "a_b",
        )

    def test_normalize_oauth_username_strips_leading_trailing_underscores(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_oauth_username("__ab__"),
            "ab0",
        )

    def test_normalize_oauth_username_empty_becomes_user(self) -> None:
        self.assertEqual(AuthServiceNormalizers.normalize_oauth_username(""), "user")
        self.assertEqual(AuthServiceNormalizers.normalize_oauth_username("   "), "user")
        self.assertEqual(AuthServiceNormalizers.normalize_oauth_username("---"), "user")

    def test_normalize_oauth_username_none_becomes_user(self) -> None:
        self.assertEqual(AuthServiceNormalizers.normalize_oauth_username(None), "user")

    def test_normalize_oauth_username_too_long_truncated(self) -> None:
        long_name = "a" * (MAX_USERNAME_LENGTH + 10)
        result = AuthServiceNormalizers.normalize_oauth_username(long_name)
        self.assertLessEqual(len(result), MAX_USERNAME_LENGTH)
        self.assertTrue(result.isalnum() or result.replace("_", "").isalnum())

    def test_normalize_oauth_username_too_short_padded_with_zeros(self) -> None:
        result = AuthServiceNormalizers.normalize_oauth_username("ab")
        self.assertEqual(len(result), MIN_USERNAME_LENGTH)
        self.assertEqual(result, "ab0")

    def test_normalize_oauth_username_exactly_min_length_unchanged(self) -> None:
        base = "abc"
        self.assertGreaterEqual(len(base), MIN_USERNAME_LENGTH)
        self.assertEqual(AuthServiceNormalizers.normalize_oauth_username(base), "abc")

    def test_normalize_oauth_username_email_prefix_style(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_oauth_username("user.name+tag"),
            "user_name_tag",
        )

    def test_normalize_oauth_username_preserves_allowed_chars(self) -> None:
        self.assertEqual(
            AuthServiceNormalizers.normalize_oauth_username("user_123"),
            "user_123",
        )
