import asyncio
import logging
from typing import Protocol

import httpx

from .types import RequestOperation


class RetryPolicy(Protocol):
    """Протокол стратегии повторных попыток для HTTP-операции."""

    async def run(
        self,
        operation: RequestOperation,
        *,
        method: str,
        url: str,
        timeout: float,
        logger: logging.Logger | None = None,
    ) -> httpx.Response:
        """Метод выполнения операции с учётом политики повторов.

        Args:
            operation: Асинхронная операция.
            method: HTTP-метод.
            url: URL для логов.
            timeout: Таймаут в секундах.
            logger: Логгер для сообщений.

        Returns:
            Ответ HTTP.
        """
        ...


class NoRetryPolicy:
    """Политика без повторных попыток."""

    async def run(
        self,
        operation: RequestOperation,
        *,
        method: str,
        url: str,
        timeout: float,
        logger: logging.Logger | None = None,
    ) -> httpx.Response:
        """Метод выполнения операции без повторов.

        Args:
            operation: Асинхронная операция.
            method: HTTP-метод.
            url: URL для логов.
            timeout: Таймаут в секундах.
            logger: Логгер для сообщений.

        Returns:
            Ответ HTTP.
        """
        return await operation()


class ExponentialBackoffRetryPolicy:
    """Политика повторных попыток с экспоненциальной задержкой."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay_seconds: float = 0.2,
        retry_on: tuple[type[Exception], ...] = (httpx.TimeoutException, httpx.RequestError),
    ) -> None:
        """Инициализация политики повторов.

        Args:
            max_attempts: Максимальное число попыток.
            base_delay_seconds: Базовая задержка между попытками (сек).
            retry_on: Типы исключений, при которых выполняется повтор.
        """
        self.max_attempts = max(1, max_attempts)
        self.base_delay_seconds = max(0.0, base_delay_seconds)
        self.retry_on = retry_on

    async def run(
        self,
        operation: RequestOperation,
        *,
        method: str,
        url: str,
        timeout: float,
        logger: logging.Logger | None = None,
    ) -> httpx.Response:
        """Метод выполнения операции с повторами при транзиентных ошибках.

        Args:
            operation: Асинхронная операция.
            method: HTTP-метод.
            url: URL для логов.
            timeout: Таймаут в секундах.
            logger: Логгер для предупреждений о повторах.

        Returns:
            Ответ HTTP.

        Raises:
            Исключение последней неудачной попытки при исчерпании повторов.
        """
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return await operation()
            except self.retry_on as exc:
                last_error = exc
                if attempt >= self.max_attempts:
                    raise
                delay = self.base_delay_seconds * (2 ** (attempt - 1))
                if logger is not None:
                    logger.warning(
                        f"HTTP {method} {url} transient failure, "
                        f"retry {attempt}/{self.max_attempts} in {delay:.2f}s (timeout={timeout}s): {exc}",
                    )
                await asyncio.sleep(delay)
        if last_error is not None:
            raise last_error
        return await operation()
