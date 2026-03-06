from unittest import TestCase

from app.core.request.sanitizers import SensitiveQueryUrlSanitizer


class TestSensitiveQueryUrlSanitizer(TestCase):
    """Тесты для SensitiveQueryUrlSanitizer."""

    def setUp(self):
        """Настройка тестового окружения."""
        self.sanitizer = SensitiveQueryUrlSanitizer()

    def test_sanitize_returns_url_unchanged_when_no_query(self):
        """URL без query-строки возвращается без изменений."""
        url = "https://api.example.com/path"
        self.assertEqual(self.sanitizer.sanitize(url), url)

    def test_sanitize_masks_access_token(self):
        """Параметр access_token маскируется как ***."""
        url = "https://api.example.com/callback?access_token=secret123&state=ok"
        result = self.sanitizer.sanitize(url)
        self.assertIn("access_token=***", result)
        self.assertIn("state=ok", result)
        self.assertNotIn("secret123", result)

    def test_sanitize_masks_code(self):
        """Параметр code маскируется."""
        url = "https://oauth.example.com/callback?code=abc123&state=x"
        result = self.sanitizer.sanitize(url)
        self.assertIn("code=***", result)
        self.assertNotIn("abc123", result)

    def test_sanitize_masks_password(self):
        """Параметр password маскируется."""
        url = "https://api.example.com/login?user=john&password=secret"
        result = self.sanitizer.sanitize(url)
        self.assertIn("password=***", result)
        self.assertIn("user=john", result)
        self.assertNotIn("secret", result)

    def test_sanitize_preserves_non_sensitive_params(self):
        """Нечувствительные параметры сохраняются."""
        url = "https://api.example.com?foo=bar&baz=qux"
        result = self.sanitizer.sanitize(url)
        self.assertIn("foo=bar", result)
        self.assertIn("baz=qux", result)

    def test_sanitize_case_insensitive_sensitive_keys(self):
        """Чувствительные ключи ищутся без учёта регистра."""
        url = "https://api.example.com?TOKEN=xyz&Token=abc"
        result = self.sanitizer.sanitize(url)
        self.assertIn("***", result)
        self.assertNotIn("xyz", result)
        self.assertNotIn("abc", result)

    def test_sanitize_invalid_url_returns_original(self):
        """При невалидном URL возвращается исходная строка (логирование не ломает запрос)."""
        invalid_url = "not-a-valid-url://[broken"
        result = self.sanitizer.sanitize(invalid_url)
        self.assertEqual(result, invalid_url)
