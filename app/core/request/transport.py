import logging
from typing import Any

import httpx

from .retry import NoRetryPolicy, RetryPolicy
from .types import Cookies, Headers, Params, RequestContent, RequestData, RequestFiles, RequestJson


class AsyncHttpTransport:
    """Низкоуровневый HTTP-транспорт с повторами и закрытием клиента."""

    def __init__(
        self,
        timeout: float = 10.0,
        verify: bool = True,
        retry_policy: RetryPolicy | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Инициализация транспорта.

        Args:
            timeout: Таймаут запроса в секундах.
            verify: Проверка SSL-сертификата.
            retry_policy: Политика повторных попыток.
            logger: Логгер для сообщений.
        """
        self.timeout = timeout
        self.verify = verify
        self.retry_policy = retry_policy or NoRetryPolicy()
        self.logger = logger
        self._client = httpx.AsyncClient(timeout=self.timeout, verify=self.verify)

    async def request(
        self,
        *,
        method: str,
        url: str,
        log_url: str | None = None,
        headers: Headers | None = None,
        params: Params | None = None,
        cookies: Cookies | None = None,
        data: RequestData | None = None,
        json_data: RequestJson | None = None,
        files: RequestFiles | None = None,
        content: RequestContent | None = None,
        follow_redirects: bool | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Метод выполнения HTTP-запроса с учётом политики повторов.

        Args:
            method: HTTP-метод.
            url: URL запроса.
            log_url: URL для логирования (если отличается от url).
            headers: Заголовки.
            params: Query-параметры.
            cookies: Куки.
            data: Тело запроса (form).
            json_data: Тело запроса (JSON).
            files: Файлы для загрузки.
            content: Сырое тело запроса.
            follow_redirects: Следовать ли редиректам.
            timeout: Таймаут в секундах.

        Returns:
            Ответ HTTP.
        """
        timeout_value = timeout if timeout is not None else self.timeout

        async def _request_once() -> httpx.Response:
            return await self._client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                cookies=cookies,
                data=data,
                json=json_data,
                files=files,
                content=content,
                follow_redirects=follow_redirects,
                timeout=timeout_value,
                **kwargs,
            )

        return await self.retry_policy.run(
            _request_once,
            method=method,
            url=log_url or url,
            timeout=timeout_value,
            logger=self.logger,
        )

    async def aclose(self) -> None:
        """Закрывает HTTP-клиент."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHttpTransport":
        """Вход в контекстный менеджер.

        Returns:
            self.
        """
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Выход из контекстного менеджера."""
        await self.aclose()
