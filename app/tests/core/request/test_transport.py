import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.core.request.retry import NoRetryPolicy
from app.core.request.transport import AsyncHttpTransport


def _run_async(coro):
    """Запуск корутины в цикле событий."""
    return asyncio.run(coro)


class TestAsyncHttpTransport(TestCase):
    """Тесты для AsyncHttpTransport."""

    @patch("app.core.request.transport.httpx.AsyncClient")
    def test_request_delegates_to_retry_policy_and_client(self, mock_client_cls):
        """request() вызывает retry_policy.run и внутри — client.request с переданными параметрами."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_client_cls.return_value.request = AsyncMock(return_value=mock_response)

        transport = AsyncHttpTransport(timeout=5.0)
        result = _run_async(
            transport.request(
                method="GET",
                url="https://api.example.com/users",
                headers={"X-Custom": "value"},
                timeout=6.0,
            )
        )

        self.assertIs(result, mock_response)
        mock_client_cls.return_value.request.assert_awaited_once()
        call_kwargs = mock_client_cls.return_value.request.call_args[1]
        self.assertEqual(call_kwargs["method"], "GET")
        self.assertEqual(call_kwargs["url"], "https://api.example.com/users")
        self.assertEqual(call_kwargs["headers"], {"X-Custom": "value"})
        self.assertEqual(call_kwargs["timeout"], 6.0)

    @patch("app.core.request.transport.httpx.AsyncClient")
    def test_request_uses_log_url_for_retry_policy(self, mock_client_cls):
        """При переданном log_url в retry_policy.run передаётся log_url, а не url."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_client_cls.return_value.request = AsyncMock(return_value=mock_response)

        mock_retry = MagicMock(spec=NoRetryPolicy)
        mock_retry.run = AsyncMock(return_value=mock_response)

        transport = AsyncHttpTransport(timeout=5.0, retry_policy=mock_retry)
        _run_async(
            transport.request(
                method="GET",
                url="https://api.example.com?token=secret",
                log_url="https://api.example.com?token=***",
            )
        )

        mock_retry.run.assert_awaited_once()
        call_kwargs = mock_retry.run.call_args[1]
        self.assertEqual(call_kwargs["url"], "https://api.example.com?token=***")

    @patch("app.core.request.transport.httpx.AsyncClient")
    def test_aclose_closes_client(self, mock_client_cls):
        """aclose() закрывает HTTP-клиент."""
        mock_client_cls.return_value.aclose = AsyncMock()

        transport = AsyncHttpTransport()
        _run_async(transport.aclose())

        mock_client_cls.return_value.aclose.assert_awaited_once()

    @patch("app.core.request.transport.httpx.AsyncClient")
    def test_context_manager_returns_self_and_closes_on_exit(self, mock_client_cls):
        """async with возвращает self и при выходе вызывает aclose."""
        mock_client_cls.return_value.aclose = AsyncMock()

        async def _test():
            async with AsyncHttpTransport() as transport:
                self.assertIsInstance(transport, AsyncHttpTransport)
            mock_client_cls.return_value.aclose.assert_awaited_once()

        _run_async(_test())
