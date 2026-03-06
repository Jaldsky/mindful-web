import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock

import httpx

from app.core.request.request_base import AsyncRequestBase


def _run_async(coro):
    """Запуск корутины в цикле событий."""
    return asyncio.run(coro)


class TestAsyncRequestBaseBuildUrl(TestCase):
    """Тесты для _build_url (через публичные методы с подставленным transport)."""

    def test_build_url_absolute_url_returned_unchanged(self):
        """Абсолютный URL возвращается без изменений."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status = MagicMock()
        mock_transport = MagicMock()
        mock_transport.request = AsyncMock(return_value=mock_response)

        client = AsyncRequestBase(base_url="https://api.example.com", transport=mock_transport)
        # _build_url вызывается внутри get; передаём абсолютный URL как endpoint
        result = _run_async(client.get("https://other.example.com/path"))

        self.assertIs(result, mock_response)
        call_kwargs = mock_transport.request.call_args[1]
        self.assertEqual(call_kwargs["url"], "https://other.example.com/path")

    def test_build_url_relative_endpoint_joined_with_base_url(self):
        """Относительный endpoint объединяется с base_url."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status = MagicMock()
        mock_transport = MagicMock()
        mock_transport.request = AsyncMock(return_value=mock_response)

        client = AsyncRequestBase(base_url="https://api.example.com", transport=mock_transport)
        _run_async(client.get("/users"))

        call_kwargs = mock_transport.request.call_args[1]
        self.assertEqual(call_kwargs["url"], "https://api.example.com/users")

    def test_build_url_relative_without_base_raises(self):
        """Относительный endpoint при пустом base_url приводит к ValueError."""
        client = AsyncRequestBase(base_url="")
        with self.assertRaises(ValueError):
            client._build_url("/path")


class TestAsyncRequestBaseGet(TestCase):
    """Тесты для метода get()."""

    def setUp(self):
        """Настройка тестового окружения."""
        self.mock_response = MagicMock(spec=httpx.Response)
        self.mock_response.raise_for_status = MagicMock()
        self.mock_transport = MagicMock()
        self.mock_transport.request = AsyncMock(return_value=self.mock_response)

    def test_get_calls_transport_with_method_get(self):
        """get() вызывает transport.request с method=GET."""
        client = AsyncRequestBase(
            base_url="https://api.example.com",
            transport=self.mock_transport,
        )
        _run_async(client.get("/users"))

        self.mock_transport.request.assert_awaited_once()
        call_kwargs = self.mock_transport.request.call_args[1]
        self.assertEqual(call_kwargs["method"], "GET")
        self.assertEqual(call_kwargs["url"], "https://api.example.com/users")

    def test_get_merges_default_headers_and_params(self):
        """get() мержит default_headers и default_params с переданными."""
        client = AsyncRequestBase(
            base_url="https://api.example.com",
            default_headers={"X-Default": "default"},
            default_params={"page": "1"},
            transport=self.mock_transport,
        )
        _run_async(client.get("/users", headers={"X-Request": "req"}, params={"page": "2"}))

        call_kwargs = self.mock_transport.request.call_args[1]
        self.assertEqual(call_kwargs["headers"], {"X-Default": "default", "X-Request": "req"})
        self.assertEqual(call_kwargs["params"], {"page": "2"})


class TestAsyncRequestBasePost(TestCase):
    """Тесты для метода post()."""

    def setUp(self):
        """Настройка тестового окружения."""
        self.mock_response = MagicMock(spec=httpx.Response)
        self.mock_response.raise_for_status = MagicMock()
        self.mock_transport = MagicMock()
        self.mock_transport.request = AsyncMock(return_value=self.mock_response)

    def test_post_calls_transport_with_method_post_and_body(self):
        """post() вызывает transport.request с method=POST и переданными data/json_data."""
        client = AsyncRequestBase(
            base_url="https://api.example.com",
            transport=self.mock_transport,
        )
        _run_async(client.post("/users", json_data={"name": "John"}))

        call_kwargs = self.mock_transport.request.call_args[1]
        self.assertEqual(call_kwargs["method"], "POST")
        self.assertEqual(call_kwargs["json_data"], {"name": "John"})


class TestAsyncRequestBaseContextManager(TestCase):
    """Тесты для контекстного менеджера."""

    def test_context_manager_returns_self_and_closes_transport_on_exit(self):
        """async with возвращает self и при выходе вызывает transport.aclose()."""
        mock_transport = MagicMock()
        mock_transport.request = AsyncMock()
        mock_transport.aclose = AsyncMock()

        async def _test():
            async with AsyncRequestBase(transport=mock_transport) as client:
                self.assertIsInstance(client, AsyncRequestBase)
            mock_transport.aclose.assert_awaited_once()

        _run_async(_test())


class TestAsyncRequestBaseSafeUrl(TestCase):
    """Тесты для использования url_sanitizer в логах (log_url)."""

    def test_transport_receives_sanitized_url_as_log_url(self):
        """В transport.request передаётся log_url с замаскированными чувствительными параметрами."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status = MagicMock()
        mock_transport = MagicMock()
        mock_transport.request = AsyncMock(return_value=mock_response)

        client = AsyncRequestBase(
            base_url="https://api.example.com",
            transport=mock_transport,
        )
        _run_async(client.get("https://api.example.com/callback?code=secret&state=ok"))

        call_kwargs = mock_transport.request.call_args[1]
        self.assertEqual(call_kwargs["url"], "https://api.example.com/callback?code=secret&state=ok")
        self.assertIn("code=***", call_kwargs["log_url"])
        self.assertIn("state=ok", call_kwargs["log_url"])
        self.assertNotIn("secret", call_kwargs["log_url"])
