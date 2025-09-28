import time
import logging
from fastapi import Request
from fastapi.responses import Response

logger = logging.getLogger(__name__)

_REQUEST_LOG_FORMAT = "Method: {method} | URL: {url} | Duration: {duration:.5f}s"


async def log_requests_middleware(request: Request, call_next):
    """Метод для Middleware логирования всех входящих HTTP-запросов и исходящих ответов.

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
        log_message = _REQUEST_LOG_FORMAT.format(method=request.method, url=request.url, duration=process_time)
        logger.info(f"Response: {response.status_code} | {log_message}")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        log_message = _REQUEST_LOG_FORMAT.format(method=request.method, url=request.url, duration=process_time)
        logger.error(f"Error: {e} | {log_message}")
        raise
