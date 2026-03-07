from unittest import TestCase
from app.services.auth.constants import (
    MAX_OAUTH_CODE_LENGTH,
    MAX_OAUTH_CODE_VERIFIER_LENGTH,
    MAX_OAUTH_STATE_LENGTH,
    MAX_PASSWORD_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_OAUTH_CODE_VERIFIER_LENGTH,
)
from app.services.auth.exceptions import (
    InvalidEmailFormatException,
    InvalidOAuthCodeFormatException,
    InvalidOAuthCodeVerifierFormatException,
    InvalidOAuthRedirectUriFormatException,
    InvalidOAuthStateFormatException,
    InvalidPasswordFormatException,
    InvalidUsernameFormatException,
    InvalidVerificationCodeFormatException,
    OAuthRedirectUriMismatchException,
    TokenInvalidException,
)
from app.services.auth.validators import AuthServiceValidators


class TestAuthServiceValidators(TestCase):
    """Тесты валидаторов auth-сервиса."""

    def test_validate_username_too_short(self):
        """Тест валидации username слишком короткого."""
        with self.assertRaises(InvalidUsernameFormatException):
            AuthServiceValidators.validate_username("ab")

    def test_validate_username_too_long(self):
        """Тест валидации username слишком длинного."""
        long_username = "a" * (MAX_USERNAME_LENGTH + 1)
        with self.assertRaises(InvalidUsernameFormatException):
            AuthServiceValidators.validate_username(long_username)

    def test_validate_username_valid_min_length(self):
        """Тест валидации username минимальной длины."""
        try:
            AuthServiceValidators.validate_username("abc")
        except InvalidUsernameFormatException:
            self.fail("validate() raised InvalidUsernameFormatException unexpectedly!")

    def test_validate_username_valid_max_length(self):
        """Тест валидации username максимальной длины."""
        valid_username = "a" * MAX_USERNAME_LENGTH
        try:
            AuthServiceValidators.validate_username(valid_username)
        except InvalidUsernameFormatException:
            self.fail("validate() raised InvalidUsernameFormatException unexpectedly!")

    def test_validate_username_with_uppercase(self):
        """Тест валидации username с заглавными буквами (валидатор не нормализует)."""
        with self.assertRaises(InvalidUsernameFormatException):
            AuthServiceValidators.validate_username("TestUser")

    def test_validate_username_with_invalid_chars(self):
        """Тест валидации username с недопустимыми символами."""
        with self.assertRaises(InvalidUsernameFormatException):
            AuthServiceValidators.validate_username("test-user")

    def test_validate_username_starts_with_underscore(self):
        """Тест валидации username начинающегося с underscore."""
        with self.assertRaises(InvalidUsernameFormatException):
            AuthServiceValidators.validate_username("_testuser")

    def test_validate_username_ends_with_underscore(self):
        """Тест валидации username заканчивающегося на underscore."""
        with self.assertRaises(InvalidUsernameFormatException):
            AuthServiceValidators.validate_username("testuser_")

    def test_validate_email_empty(self):
        """Тест валидации пустого email."""
        with self.assertRaises(InvalidEmailFormatException):
            AuthServiceValidators.validate_email("")

    def test_validate_email_invalid_format(self):
        """Тест валидации email с неверным форматом."""
        with self.assertRaises(InvalidEmailFormatException):
            AuthServiceValidators.validate_email("invalid-email")

    def test_validate_email_valid(self):
        """Тест валидации валидного email."""
        try:
            AuthServiceValidators.validate_email("test@example.com")
        except InvalidEmailFormatException:
            self.fail("validate() raised InvalidEmailFormatException unexpectedly!")

    def test_validate_password_too_short(self):
        """Тест валидации password слишком короткого."""
        with self.assertRaises(InvalidPasswordFormatException):
            AuthServiceValidators.validate_password("pass123")

    def test_validate_password_too_long(self):
        """Тест валидации password слишком длинного."""
        long_password = "a" * (MAX_PASSWORD_LENGTH + 1) + "1"
        with self.assertRaises(InvalidPasswordFormatException):
            AuthServiceValidators.validate_password(long_password)

    def test_validate_password_no_letters(self):
        """Тест валидации password без букв."""
        with self.assertRaises(InvalidPasswordFormatException):
            AuthServiceValidators.validate_password("12345678")

    def test_validate_password_no_digits(self):
        """Тест валидации password без цифр."""
        with self.assertRaises(InvalidPasswordFormatException):
            AuthServiceValidators.validate_password("password")

    def test_validate_password_valid(self):
        """Тест валидации валидного password."""
        try:
            AuthServiceValidators.validate_password("password123")
        except InvalidPasswordFormatException:
            self.fail("validate() raised InvalidPasswordFormatException unexpectedly!")

    def test_validate_verification_code_valid(self):
        """Тест валидации валидного кода подтверждения."""
        try:
            AuthServiceValidators.validate_verification_code("123456")
        except InvalidVerificationCodeFormatException:
            self.fail("validate_verification_code() raised InvalidVerificationCodeFormatException unexpectedly!")

    def test_validate_verification_code_trims_spaces(self):
        """Валидатор не нормализует вход: пробелы делают код невалидным."""
        with self.assertRaises(InvalidVerificationCodeFormatException):
            AuthServiceValidators.validate_verification_code("  123456  ")

    def test_validate_verification_code_invalid_length(self):
        """Тест валидации кода неверной длины."""
        with self.assertRaises(InvalidVerificationCodeFormatException):
            AuthServiceValidators.validate_verification_code("12345")

    def test_validate_verification_code_non_digits(self):
        """Тест валидации кода с нецифровыми символами."""
        with self.assertRaises(InvalidVerificationCodeFormatException):
            AuthServiceValidators.validate_verification_code("12ab56")

    def test_validate_jwt_token_empty(self):
        """Пустой токен должен считаться невалидным."""
        with self.assertRaises(TokenInvalidException):
            AuthServiceValidators.validate_jwt_token("")

    def test_validate_jwt_token_valid(self):
        """Непустой токен валиден на уровне первичной валидации."""
        try:
            AuthServiceValidators.validate_jwt_token("some.jwt.token")
        except TokenInvalidException:
            self.fail("validate_jwt_token() raised TokenInvalidException unexpectedly!")

    def test_validate_oauth_code_empty(self):
        """Пустой OAuth code должен вызывать исключение."""
        with self.assertRaises(InvalidOAuthCodeFormatException):
            AuthServiceValidators.validate_oauth_code("")

    def test_validate_oauth_code_too_long(self):
        """OAuth code длиннее MAX_OAUTH_CODE_LENGTH должен вызывать исключение."""
        long_code = "a" * (MAX_OAUTH_CODE_LENGTH + 1)
        with self.assertRaises(InvalidOAuthCodeFormatException):
            AuthServiceValidators.validate_oauth_code(long_code)

    def test_validate_oauth_code_valid(self):
        """Валидный OAuth code не должен вызывать исключение."""
        try:
            AuthServiceValidators.validate_oauth_code("4/0AbCdEfGhIjKlMnOpQr")
        except InvalidOAuthCodeFormatException:
            self.fail("validate_oauth_code() raised InvalidOAuthCodeFormatException unexpectedly!")

    def test_validate_oauth_redirect_uri_invalid_scheme(self):
        """Redirect URI с недопустимой схемой (не http/https) должен вызывать исключение."""
        with self.assertRaises(InvalidOAuthRedirectUriFormatException):
            AuthServiceValidators.validate_oauth_redirect_uri("ftp://example.com/callback")

    def test_validate_oauth_redirect_uri_no_netloc(self):
        """Redirect URI без netloc должен вызывать исключение."""
        with self.assertRaises(InvalidOAuthRedirectUriFormatException):
            AuthServiceValidators.validate_oauth_redirect_uri("https:///path")

    def test_validate_oauth_redirect_uri_valid_http(self):
        """Валидный HTTP redirect URI не должен вызывать исключение."""
        try:
            AuthServiceValidators.validate_oauth_redirect_uri("http://localhost:8000/oauth/callback")
        except InvalidOAuthRedirectUriFormatException:
            self.fail("validate_oauth_redirect_uri() raised InvalidOAuthRedirectUriFormatException unexpectedly!")

    def test_validate_oauth_redirect_uri_valid_https(self):
        """Валидный HTTPS redirect URI не должен вызывать исключение."""
        try:
            AuthServiceValidators.validate_oauth_redirect_uri("https://app.example.com/oauth/google/callback")
        except InvalidOAuthRedirectUriFormatException:
            self.fail("validate_oauth_redirect_uri() raised InvalidOAuthRedirectUriFormatException unexpectedly!")

    def test_validate_oauth_redirect_uri_matches_none_expected_passes(self):
        """Если expected_redirect_uri None или пустой, проверка не выполняется."""
        try:
            AuthServiceValidators.validate_oauth_redirect_uri_matches(None, "http://any.com/cb")
            AuthServiceValidators.validate_oauth_redirect_uri_matches("", "http://any.com/cb")
        except OAuthRedirectUriMismatchException:
            self.fail("validate_oauth_redirect_uri_matches() raised OAuthRedirectUriMismatchException unexpectedly!")

    def test_validate_oauth_redirect_uri_matches_same_passes(self):
        """Если URI совпадают, исключение не выбрасывается."""
        uri = "https://app.example.com/oauth/callback"
        try:
            AuthServiceValidators.validate_oauth_redirect_uri_matches(uri, uri)
        except OAuthRedirectUriMismatchException:
            self.fail("validate_oauth_redirect_uri_matches() raised OAuthRedirectUriMismatchException unexpectedly!")

    def test_validate_oauth_redirect_uri_matches_different_raises(self):
        """Если expected и фактический URI различаются, выбрасывается OAuthRedirectUriMismatchException."""
        with self.assertRaises(OAuthRedirectUriMismatchException):
            AuthServiceValidators.validate_oauth_redirect_uri_matches(
                "https://app.example.com/callback",
                "https://evil.com/callback",
            )

    def test_validate_oauth_code_verifier_none_passes(self):
        """code_verifier=None допустим (PKCE опционален)."""
        try:
            AuthServiceValidators.validate_oauth_code_verifier(None)
        except InvalidOAuthCodeVerifierFormatException:
            self.fail("validate_oauth_code_verifier() raised unexpectedly for None!")

    def test_validate_oauth_code_verifier_empty_raises(self):
        """Пустая строка code_verifier должна вызывать исключение."""
        with self.assertRaises(InvalidOAuthCodeVerifierFormatException):
            AuthServiceValidators.validate_oauth_code_verifier("")

    def test_validate_oauth_code_verifier_too_short_raises(self):
        """code_verifier короче MIN_OAUTH_CODE_VERIFIER_LENGTH должен вызывать исключение."""
        short = "a" * (MIN_OAUTH_CODE_VERIFIER_LENGTH - 1)
        with self.assertRaises(InvalidOAuthCodeVerifierFormatException):
            AuthServiceValidators.validate_oauth_code_verifier(short)

    def test_validate_oauth_code_verifier_too_long_raises(self):
        """code_verifier длиннее MAX_OAUTH_CODE_VERIFIER_LENGTH должен вызывать исключение."""
        long_verifier = "a" * (MAX_OAUTH_CODE_VERIFIER_LENGTH + 1)
        with self.assertRaises(InvalidOAuthCodeVerifierFormatException):
            AuthServiceValidators.validate_oauth_code_verifier(long_verifier)

    def test_validate_oauth_code_verifier_invalid_chars_raises(self):
        """code_verifier с недопустимыми символами должен вызывать исключение."""
        with self.assertRaises(InvalidOAuthCodeVerifierFormatException):
            AuthServiceValidators.validate_oauth_code_verifier("a" * 43 + "!")

    def test_validate_oauth_code_verifier_valid(self):
        """Валидный code_verifier (длина и символы из разрешённого набора) не должен вызывать исключение."""
        valid = "a" * MIN_OAUTH_CODE_VERIFIER_LENGTH
        try:
            AuthServiceValidators.validate_oauth_code_verifier(valid)
        except InvalidOAuthCodeVerifierFormatException:
            self.fail("validate_oauth_code_verifier() raised unexpectedly for valid verifier!")

    def test_validate_oauth_code_verifier_valid_with_allowed_chars(self):
        """code_verifier с буквами, цифрами и -._~ допустим."""
        valid = "ABCDefgh1234-._~" + "x" * (MIN_OAUTH_CODE_VERIFIER_LENGTH - 16)
        try:
            AuthServiceValidators.validate_oauth_code_verifier(valid)
        except InvalidOAuthCodeVerifierFormatException:
            self.fail("validate_oauth_code_verifier() raised unexpectedly for allowed chars!")

    def test_validate_oauth_state_none_passes(self):
        """state=None допустим."""
        try:
            AuthServiceValidators.validate_oauth_state(None)
        except InvalidOAuthStateFormatException:
            self.fail("validate_oauth_state() raised unexpectedly for None!")

    def test_validate_oauth_state_empty_raises(self):
        """Пустая строка state должна вызывать исключение."""
        with self.assertRaises(InvalidOAuthStateFormatException):
            AuthServiceValidators.validate_oauth_state("")

    def test_validate_oauth_state_too_long_raises(self):
        """state длиннее MAX_OAUTH_STATE_LENGTH должен вызывать исключение."""
        long_state = "a" * (MAX_OAUTH_STATE_LENGTH + 1)
        with self.assertRaises(InvalidOAuthStateFormatException):
            AuthServiceValidators.validate_oauth_state(long_state)

    def test_validate_oauth_state_valid(self):
        """Валидный state не должен вызывать исключение."""
        try:
            AuthServiceValidators.validate_oauth_state("random-state-value")
        except InvalidOAuthStateFormatException:
            self.fail("validate_oauth_state() raised unexpectedly for valid state!")

    def test_validate_oauth_state_max_length_passes(self):
        """state длины MAX_OAUTH_STATE_LENGTH допустим."""
        try:
            AuthServiceValidators.validate_oauth_state("a" * MAX_OAUTH_STATE_LENGTH)
        except InvalidOAuthStateFormatException:
            self.fail("validate_oauth_state() raised unexpectedly for max length state!")
