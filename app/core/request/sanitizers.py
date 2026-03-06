from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class UrlSanitizer(Protocol):
    """Протокол стратегии очистки URL в логах."""

    def sanitize(self, url: str) -> str:
        """Метод очистки URL для безопасного логирования.

        Args:
            url: Исходный URL.

        Returns:
            URL, безопасный для вывода в логи.
        """
        ...


class SensitiveQueryUrlSanitizer:
    """Санитайзер чувствительных query-параметров в URL."""

    _SENSITIVE_QUERY_KEYS = frozenset(
        {
            "access_token",
            "id_token",
            "refresh_token",
            "token",
            "authorization",
            "code",
            "client_secret",
            "secret",
            "password",
        }
    )

    def sanitize(self, url: str) -> str:
        """Метод очистки URL от чувствительных query-параметров для логов.

        Args:
            url: Исходный URL.

        Returns:
            URL с замаскированными чувствительными параметрами.
        """
        try:
            parsed = urlsplit(url)
            if not parsed.query:
                return url

            sanitized_query: list[tuple[str, str]] = []
            for key, value in parse_qsl(parsed.query, keep_blank_values=True):
                if key.lower() in self._SENSITIVE_QUERY_KEYS:
                    sanitized_query.append((key, "***"))
                else:
                    sanitized_query.append((key, value))

            return urlunsplit(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    urlencode(sanitized_query, doseq=True).replace("%2A%2A%2A", "***"),
                    parsed.fragment,
                )
            )
        except Exception:
            return url
