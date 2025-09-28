import os
import multiprocessing

# Настройки воркеров
# Количество активных воркеров
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
# Класс воркера UvicornWorker для FastAPI + Gunicorn
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "uvicorn.workers.UvicornWorker")
# Количество потоков 1 для FastAPI + Gunicorn
threads = int(os.getenv("GUNICORN_THREADS", 1))
# Время на завершение воркеров при рестарте
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", 60))
# Максимальное количество запросов на воркер перед рестартом
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", 1000))
# Случайный разброс рестарта, помогает избежать одновременного рестарта всех воркеров
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", 50))

# Сетевые настройки
# Привязка к интерфейсу и порту
# Привязка к интерфейсу и порту
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
# Размер очереди подключений
backlog = int(os.getenv("GUNICORN_BACKLOG", 2048))
# Таймаут обработки запроса
timeout = int(os.getenv("GUNICORN_TIMEOUT", 60))
# Время keep-alive соединений
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 4))

# Настройки логгирования
# Логи доступа, запись в stdout
accesslog = os.getenv("GUNICORN_ACCESSLOG", "-")
# Логи ошибок, запись в stdout
errorlog = os.getenv("GUNICORN_ERRORLOG", "-")
# Уровень логирования, debug, info, warning, error, critical
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")

# Настройки безопасности
# Максимальная длина URL
limit_request_line = int(os.getenv("GUNICORN_LIMIT_REQUEST_LINE", 2048))
# Максимальное число заголовков
limit_request_fields = int(os.getenv("GUNICORN_LIMIT_REQUEST_FIELDS", 20))
# Протокол прокси, True если за reverse proxy
proxy_protocol = bool(os.getenv("GUNICORN_PROXY_PROTOCOL", False))
# Список разрешенных IP
proxy_allow_ips = os.getenv("GUNICORN_PROXY_ALLOW_IPS", "*")
