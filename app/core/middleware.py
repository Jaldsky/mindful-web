import time
import logging
from fastapi import Request
from fastapi.responses import Response

from ..config import ACCEPT_LANGUAGE_HEADER, DEFAULT_LOCALE

logger = logging.getLogger(__name__)


async def locale_middleware(
    request: Request,
    call_next,
    header: str = ACCEPT_LANGUAGE_HEADER,
    default_locale: str = DEFAULT_LOCALE,
):
    """Функция для Middleware выставления локализации из заголовка Accept-Language.

    Парсит первый тег языка (формат: en-US,en;q=0.9,ru;q=0.8 -> en-US) и кладёт
    в request.state.locale. Нормализация и валидация — в AcceptLanguageHeaderSchema
    (dependency get_accept_language). Если заголовка нет или он пустой — default_locale.

    Args:
        request: Объект входящего HTTP-запроса.
        call_next: Функция для передачи запроса следующему обработчику в цепочке middleware.
        header: Имя HTTP-заголовка с языком.
        default_locale: Локаль по умолчанию при отсутствии заголовка.

    Returns:
        Объект HTTP-ответа после обработки запроса.
    """
    raw = request.headers.get(header)
    if not raw or not raw.strip():
        request.state.locale = default_locale
        return await call_next(request)

    request.state.locale = raw.strip().split(",")[0].strip().split(";")[0].strip() or default_locale
    return await call_next(request)


async def log_requests_middleware(request: Request, call_next):
    """Функция для Middleware логирования всех входящих HTTP-запросов и исходящих ответов.

    Логирует метод и URL каждого запроса до его обработки, а также статус-код,
    метод, URL и длительность обработки после получения ответа. В случае возникновения
    исключения во время обработки запроса, логирует ошибку с теми же метаданными.

    Args:
        request: Объект входящего HTTP-запроса.
        call_next: Функция для передачи запроса следующему обработчику в цепочке middleware.

    Returns:
        Объект HTTP-ответа после обработки запроса.

    Raises:
        Любое исключение, возникшее при обработке запроса, будет залогировано и повторно выброшено.
    """
    logger.info(f"Request: {request.method} {request.url}")

    start_time = time.time()

    try:
        response: Response = await call_next(request)
        process_time = time.time() - start_time
        log_message = f"Method: {request.method} | URL: {request.url} | Duration: {process_time:.5f}s"
        logger.info(f"Response: {response.status_code} | {log_message}")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        log_message = f"Method: {request.method} | URL: {request.url} | Duration: {process_time:.5f}s"
        logger.error(f"Error: {e} | {log_message}")
        raise
