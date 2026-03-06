import asyncio
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from starlette.responses import Response

from app.main import app
from app.core.middleware import locale_middleware
from app.config import DEFAULT_LOCALE


class TestLocaleMiddleware(TestCase):
    """Тесты для locale_middleware."""

    def _run_async(self, coro):
        return asyncio.run(coro)

    def test_locale_from_accept_language_single_tag(self):
        """Заголовок с одним тегом — request.state.locale равен этому тегу."""
        request = MagicMock()
        request.headers.get = MagicMock(return_value="ru")
        request.state = SimpleNamespace()
        captured = []

        async def call_next(req):
            captured.append(getattr(req.state, "locale", None))
            return Response()

        self._run_async(locale_middleware(request, call_next))
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0], "ru")

    def test_locale_from_accept_language_with_quality(self):
        """Заголовок en-US,en;q=0.9 — берётся первый тег en-US (нормализация в схеме)."""
        request = MagicMock()
        request.headers.get = MagicMock(return_value="en-US,en;q=0.9,ru;q=0.8")
        request.state = SimpleNamespace()
        captured = []

        async def call_next(req):
            captured.append(getattr(req.state, "locale", None))
            return Response()

        self._run_async(locale_middleware(request, call_next))
        self.assertEqual(captured[0], "en-US")

    def test_locale_default_when_header_missing(self):
        """Нет заголовка — request.state.locale равен default_locale (en)."""
        request = MagicMock()
        request.headers.get = MagicMock(return_value=None)
        request.state = SimpleNamespace()
        captured = []

        async def call_next(req):
            captured.append(getattr(req.state, "locale", None))
            return Response()

        self._run_async(locale_middleware(request, call_next))
        self.assertEqual(captured[0], DEFAULT_LOCALE)

    def test_locale_default_when_header_empty(self):
        """Пустой или пробельный заголовок — request.state.locale равен default_locale."""
        request = MagicMock()
        request.state = SimpleNamespace()
        captured = []

        async def call_next(req):
            captured.append(getattr(req.state, "locale", None))
            return Response()

        for raw in ("", "   "):
            with self.subTest(raw=repr(raw)):
                request.headers.get = MagicMock(return_value=raw)
                captured.clear()
                self._run_async(locale_middleware(request, call_next))
                self.assertEqual(captured[0], DEFAULT_LOCALE)

    def test_locale_default_when_parsed_empty(self):
        """Заголовок без валидного тега (только запятые/точка с запятой) — default_locale."""
        request = MagicMock()
        request.headers.get = MagicMock(return_value="; , ")
        request.state = SimpleNamespace()
        captured = []

        async def call_next(req):
            captured.append(getattr(req.state, "locale", None))
            return Response()

        self._run_async(locale_middleware(request, call_next))
        self.assertEqual(captured[0], DEFAULT_LOCALE)

    def test_locale_uses_custom_header_and_default(self):
        """Кастомные header и default_locale передаются в middleware."""
        request = MagicMock()
        request.headers.get = MagicMock(return_value=None)
        request.state = SimpleNamespace()
        captured = []

        async def call_next(req):
            captured.append(getattr(req.state, "locale", None))
            return Response()

        self._run_async(
            locale_middleware(
                request,
                call_next,
                header="x-custom-lang",
                default_locale="de",
            )
        )
        request.headers.get.assert_called_once_with("x-custom-lang")
        self.assertEqual(captured[0], "de")


class TestMiddleware(TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("app.core.middleware.logger")
    def test_middleware_logs_successful_request(self, mock_logger: MagicMock):
        response = self.client.get("/api/v1/healthcheck")

        assert response.status_code == 200

        # Проверяем, что logger.info вызывался дважды:
        # 1. При входе в запрос
        # 2. При успешном ответе
        assert mock_logger.info.call_count == 2

        request_log = mock_logger.info.call_args_list[0][0][0]
        response_log = mock_logger.info.call_args_list[1][0][0]

        assert "Request: GET http://testserver/api/v1/healthcheck" in request_log
        assert "Response: 200" in response_log
        assert "Method: GET" in response_log
        assert "Duration:" in response_log

    @patch("app.core.middleware.logger")
    def test_middleware_logs_error_request(self, mock_logger: MagicMock):
        response = self.client.get("/non-existent-path")

        assert response.status_code == 404

        assert mock_logger.info.call_count == 2  # вход + выход
        assert mock_logger.error.call_count == 0  # исключения не было

        request_log = mock_logger.info.call_args_list[0][0][0]
        response_log = mock_logger.info.call_args_list[1][0][0]

        assert "Request: GET http://testserver/non-existent-path" in request_log
        assert "Response: 404" in response_log
        assert "Method: GET" in response_log
        assert "URL: http://testserver/non-existent-path" in response_log
        assert "Duration:" in response_log
