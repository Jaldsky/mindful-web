import logging
from typing import Any
from urllib.parse import urljoin

import httpx

from .retry import NoRetryPolicy, RetryPolicy
from .sanitizers import SensitiveQueryUrlSanitizer, UrlSanitizer
from .transport import AsyncHttpTransport
from .types import Cookies, Headers, Params, RequestContent, RequestData, RequestFiles, RequestJson


class AsyncRequestBase:
    """Высокоуровневый асинхронный HTTP-клиент с дефолтами и безопасным логированием."""

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 10.0,
        verify: bool = True,
        default_raise_for_status: bool = True,
        default_headers: Headers | None = None,
        default_params: Params | None = None,
        retry_policy: RetryPolicy | None = None,
        url_sanitizer: UrlSanitizer | None = None,
        transport: AsyncHttpTransport | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Инициализация клиента.

        Args:
            base_url: Базовый URL для относительных endpoint.
            timeout: Таймаут запроса в секундах.
            verify: Проверка SSL-сертификата.
            default_raise_for_status: Вызывать raise_for_status по умолчанию.
            default_headers: Заголовки по умолчанию.
            default_params: Параметры по умолчанию.
            retry_policy: Политика повторных попыток.
            url_sanitizer: Санитайзер URL для логов.
            transport: HTTP-транспорт (если не задан — создаётся свой).
            logger: Логгер для запросов и ошибок.
        """
        self.base_url = base_url.rstrip("/") or ""
        self.timeout = timeout
        self.verify = verify
        self.default_raise_for_status = default_raise_for_status
        self.default_headers = dict(default_headers or {})
        self.default_params = dict(default_params or {})
        self.retry_policy = retry_policy or NoRetryPolicy()
        self.url_sanitizer = url_sanitizer or SensitiveQueryUrlSanitizer()
        self.logger = logger
        self.transport = transport or AsyncHttpTransport(
            timeout=self.timeout,
            verify=self.verify,
            retry_policy=self.retry_policy,
            logger=self.logger,
        )

    async def __aenter__(self) -> "AsyncRequestBase":
        """Вход в контекстный менеджер.

        Returns:
            self.
        """
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Выход из контекстного менеджера."""
        await self.aclose()

    def _build_url(self, endpoint: str) -> str:
        """Приватный метод сборки полного URL из endpoint.

        Args:
            endpoint: Относительный путь или абсолютный URL.

        Returns:
            Полный URL.

        Raises:
            ValueError: Если endpoint относительный, а base_url пустой.
        """
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        if not self.base_url:
            raise ValueError("Relative endpoint requires non-empty base_url")
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def _log(self, message: str) -> None:
        """Приватный метод записи сообщения в лог.

        Args:
            message: Сообщение для записи в лог.
        """
        if self.logger is None:
            return
        self.logger.info(message)

    def _safe_url(self, url: str) -> str:
        """Приватный метод получения безопасного для логов варианта URL.

        Args:
            url: Исходный URL.

        Returns:
            URL, безопасный для вывода в логи.
        """
        return self.url_sanitizer.sanitize(url)

    def _log_request_error(
        self,
        *,
        method: str,
        url: str,
        timeout: float,
        error: Exception,
    ) -> None:
        """Приватный метод логирования ошибки запроса.

        Args:
            method: HTTP-метод.
            url: URL запроса.
            timeout: Таймаут в секундах.
            error: Исключение.
        """
        if self.logger is None:
            return
        safe_url = self._safe_url(url)
        self.logger.error(
            f"HTTP {method} {safe_url} failed (timeout={timeout}s): {error}",
            exc_info=True,
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        *,
        headers: Headers | None = None,
        params: Params | None = None,
        cookies: Cookies | None = None,
        data: RequestData | None = None,
        json_data: RequestJson | None = None,
        files: RequestFiles | None = None,
        content: RequestContent | None = None,
        follow_redirects: bool | None = None,
        raise_for_status: bool | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Приватный метод выполнения HTTP-запроса с мержем дефолтов и опциональным raise_for_status.

        Args:
            method: HTTP-метод.
            endpoint: Относительный путь или абсолютный URL.
            headers: Заголовки.
            params: Query-параметры.
            cookies: Куки.
            data: Тело (form).
            json_data: Тело (JSON).
            files: Файлы.
            content: Сырое тело.
            follow_redirects: Следовать редиректам.
            raise_for_status: Вызвать response.raise_for_status().
            timeout: Таймаут в секундах.

        Returns:
            Ответ HTTP.

        Raises:
            Исключения httpx при ошибке запроса или при raise_for_status.
        """
        url = self._build_url(endpoint)
        safe_url = self._safe_url(url)
        timeout_value = timeout if timeout is not None else self.timeout
        merged_headers: Headers | None = {**self.default_headers, **(headers or {})} or None
        merged_params: Params | None = {**self.default_params, **(params or {})} or None

        try:
            response = await self.transport.request(
                method=method,
                url=url,
                log_url=safe_url,
                headers=merged_headers,
                params=merged_params,
                cookies=cookies,
                data=data,
                json_data=json_data,
                files=files,
                content=content,
                follow_redirects=follow_redirects,
                timeout=timeout_value,
                **kwargs,
            )
        except Exception as exc:
            self._log_request_error(method=method, url=url, timeout=timeout_value, error=exc)
            raise

        if raise_for_status if raise_for_status is not None else self.default_raise_for_status:
            response.raise_for_status()
        return response

    async def aclose(self) -> None:
        """Закрывает транспорт."""
        await self.transport.aclose()

    async def get(
        self,
        endpoint: str,
        headers: Headers | None = None,
        params: Params | None = None,
        cookies: Cookies | None = None,
        follow_redirects: bool | None = None,
        raise_for_status: bool | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Метод GET-запроса.

        Args:
            endpoint: Относительный путь или абсолютный URL.
            headers: Заголовки.
            params: Query-параметры.
            cookies: Куки.
            follow_redirects: Следовать редиректам.
            raise_for_status: Вызвать raise_for_status.
            timeout: Таймаут в секундах.

        Returns:
            Ответ HTTP.
        """
        return await self._make_request(
            method="GET",
            endpoint=endpoint,
            headers=headers,
            params=params,
            cookies=cookies,
            follow_redirects=follow_redirects,
            raise_for_status=raise_for_status,
            timeout=timeout,
            **kwargs,
        )

    async def post(
        self,
        endpoint: str,
        headers: Headers | None = None,
        data: RequestData | None = None,
        json_data: RequestJson | None = None,
        params: Params | None = None,
        cookies: Cookies | None = None,
        files: RequestFiles | None = None,
        content: RequestContent | None = None,
        follow_redirects: bool | None = None,
        raise_for_status: bool | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Метод POST-запроса.

        Args:
            endpoint: Относительный путь или абсолютный URL.
            headers: Заголовки.
            data: Тело (form).
            json_data: Тело (JSON).
            params: Query-параметры.
            cookies: Куки.
            files: Файлы.
            content: Сырое тело.
            follow_redirects: Следовать редиректам.
            raise_for_status: Вызвать raise_for_status.
            timeout: Таймаут в секундах.

        Returns:
            Ответ HTTP.
        """
        return await self._make_request(
            method="POST",
            endpoint=endpoint,
            headers=headers,
            data=data,
            json_data=json_data,
            params=params,
            cookies=cookies,
            files=files,
            content=content,
            follow_redirects=follow_redirects,
            raise_for_status=raise_for_status,
            timeout=timeout,
            **kwargs,
        )

    async def put(
        self,
        endpoint: str,
        headers: Headers | None = None,
        data: RequestData | None = None,
        json_data: RequestJson | None = None,
        params: Params | None = None,
        cookies: Cookies | None = None,
        files: RequestFiles | None = None,
        content: RequestContent | None = None,
        follow_redirects: bool | None = None,
        raise_for_status: bool | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Метод PUT-запроса.

        Args:
            endpoint: Относительный путь или абсолютный URL.
            headers: Заголовки.
            data: Тело (form).
            json_data: Тело (JSON).
            params: Query-параметры.
            cookies: Куки.
            files: Файлы.
            content: Сырое тело.
            follow_redirects: Следовать редиректам.
            raise_for_status: Вызвать raise_for_status.
            timeout: Таймаут в секундах.

        Returns:
            Ответ HTTP.
        """
        return await self._make_request(
            method="PUT",
            endpoint=endpoint,
            headers=headers,
            data=data,
            json_data=json_data,
            params=params,
            cookies=cookies,
            files=files,
            content=content,
            follow_redirects=follow_redirects,
            raise_for_status=raise_for_status,
            timeout=timeout,
            **kwargs,
        )

    async def patch(
        self,
        endpoint: str,
        headers: Headers | None = None,
        data: RequestData | None = None,
        json_data: RequestJson | None = None,
        params: Params | None = None,
        cookies: Cookies | None = None,
        files: RequestFiles | None = None,
        content: RequestContent | None = None,
        follow_redirects: bool | None = None,
        raise_for_status: bool | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Метод PATCH-запроса.

        Args:
            endpoint: Относительный путь или абсолютный URL.
            headers: Заголовки.
            data: Тело (form).
            json_data: Тело (JSON).
            params: Query-параметры.
            cookies: Куки.
            files: Файлы.
            content: Сырое тело.
            follow_redirects: Следовать редиректам.
            raise_for_status: Вызвать raise_for_status.
            timeout: Таймаут в секундах.

        Returns:
            Ответ HTTP.
        """
        return await self._make_request(
            method="PATCH",
            endpoint=endpoint,
            headers=headers,
            data=data,
            json_data=json_data,
            params=params,
            cookies=cookies,
            files=files,
            content=content,
            follow_redirects=follow_redirects,
            raise_for_status=raise_for_status,
            timeout=timeout,
            **kwargs,
        )

    async def delete(
        self,
        endpoint: str,
        headers: Headers | None = None,
        data: RequestData | None = None,
        json_data: RequestJson | None = None,
        params: Params | None = None,
        cookies: Cookies | None = None,
        files: RequestFiles | None = None,
        content: RequestContent | None = None,
        follow_redirects: bool | None = None,
        raise_for_status: bool | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Метод DELETE-запроса.

        Args:
            endpoint: Относительный путь или абсолютный URL.
            headers: Заголовки.
            data: Тело (form).
            json_data: Тело (JSON).
            params: Query-параметры.
            cookies: Куки.
            files: Файлы.
            content: Сырое тело.
            follow_redirects: Следовать редиректам.
            raise_for_status: Вызвать raise_for_status.
            timeout: Таймаут в секундах.

        Returns:
            Ответ HTTP.
        """
        return await self._make_request(
            method="DELETE",
            endpoint=endpoint,
            headers=headers,
            data=data,
            json_data=json_data,
            params=params,
            cookies=cookies,
            files=files,
            content=content,
            follow_redirects=follow_redirects,
            raise_for_status=raise_for_status,
            timeout=timeout,
            **kwargs,
        )
