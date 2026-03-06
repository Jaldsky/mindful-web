import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock

import httpx

from app.core.request.retry import ExponentialBackoffRetryPolicy, NoRetryPolicy


def _run_async(coro):
    """Запуск корутины в цикле событий."""
    return asyncio.run(coro)


class TestNoRetryPolicy(TestCase):
    """Тесты для NoRetryPolicy."""

    def test_run_calls_operation_once(self):
        """run() вызывает операцию один раз и возвращает её результат."""
        mock_response = MagicMock(spec=httpx.Response)
        operation = AsyncMock(return_value=mock_response)

        policy = NoRetryPolicy()
        result = _run_async(
            policy.run(
                operation,
                method="GET",
                url="https://api.example.com/",
                timeout=10.0,
                logger=None,
            )
        )

        self.assertIs(result, mock_response)
        operation.assert_awaited_once()

    def test_run_passes_through_exception(self):
        """run() пробрасывает исключение из операции."""
        operation = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        policy = NoRetryPolicy()

        with self.assertRaises(httpx.TimeoutException):
            _run_async(
                policy.run(
                    operation,
                    method="GET",
                    url="https://api.example.com/",
                    timeout=5.0,
                )
            )
        operation.assert_awaited_once()


class TestExponentialBackoffRetryPolicy(TestCase):
    """Тесты для ExponentialBackoffRetryPolicy."""

    def test_run_returns_on_first_success(self):
        """При успехе с первой попытки повтор не выполняется."""
        mock_response = MagicMock(spec=httpx.Response)
        operation = AsyncMock(return_value=mock_response)

        policy = ExponentialBackoffRetryPolicy(max_attempts=3, base_delay_seconds=0.01)

        result = _run_async(
            policy.run(
                operation,
                method="GET",
                url="https://api.example.com/",
                timeout=10.0,
            )
        )

        self.assertIs(result, mock_response)
        operation.assert_awaited_once()

    def test_run_retries_on_retry_on_exception_then_succeeds(self):
        """При транзиентной ошибке выполняется повтор; при успехе возвращается ответ."""
        mock_response = MagicMock(spec=httpx.Response)
        operation = AsyncMock(side_effect=[httpx.TimeoutException("t"), mock_response])

        policy = ExponentialBackoffRetryPolicy(max_attempts=3, base_delay_seconds=0.01)

        result = _run_async(
            policy.run(
                operation,
                method="GET",
                url="https://api.example.com/",
                timeout=10.0,
            )
        )

        self.assertIs(result, mock_response)
        self.assertEqual(operation.await_count, 2)

    def test_run_raises_after_max_attempts(self):
        """После исчерпания попыток пробрасывается последнее исключение."""
        operation = AsyncMock(side_effect=httpx.RequestError("network error"))

        policy = ExponentialBackoffRetryPolicy(max_attempts=2, base_delay_seconds=0.01)

        with self.assertRaises(httpx.RequestError):
            _run_async(
                policy.run(
                    operation,
                    method="GET",
                    url="https://api.example.com/",
                    timeout=10.0,
                )
            )

        self.assertEqual(operation.await_count, 2)

    def test_init_normalizes_max_attempts(self):
        """max_attempts меньше 1 приводится к 1."""
        policy = ExponentialBackoffRetryPolicy(max_attempts=0)
        self.assertEqual(policy.max_attempts, 1)
